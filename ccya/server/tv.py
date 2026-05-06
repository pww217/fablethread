"""Turn viewer data preparation and _tv_* helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .metrics import _fmt_tokens_exact

_STATUS_CSS: dict[str, str] = {
    "ok": "tv-sts-ok",
    "skipped": "tv-sts-skipped",
    "retried": "tv-sts-retried",
    "rejected": "tv-sts-rejected",
    "error": "tv-sts-error",
    "neutral": "tv-sts-neutral",
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
        out = json.loads(s)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = json.loads(s[i : j + 1])
                return out if isinstance(out, dict) else None
            except json.JSONDecodeError:
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
                summary = ", ".join(l for l in labels if l)
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


def _tv_rules_status(rules_ev: Any) -> str:
    if not rules_ev or not isinstance(rules_ev, dict):
        return "neutral"
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
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        narr = ev.get("narrate") or {}
        ext = ev.get("extract") or {}
        extraction = ev.get("extraction") or {}
        rej = ev.get("rejected") or []
        tid = str(ev.get("trace_id") or "")
        rules_ev = ev.get("rules") or {}

        rules_prompt = ev.get("rules_prompt") or {}
        narr_prompt = ev.get("narrate_prompt") or {}

        def _fmt_ms(ms: Any) -> str:
            if ms is None:
                return "\u2014"
            try:
                return f"{float(ms) / 1000.0:.1f}s"
            except (TypeError, ValueError):
                return "\u2014"

        rules_ev_d = rules_ev if isinstance(rules_ev, dict) else {}
        scene_blk = extraction.get("scene") or {}
        state_blk = extraction.get("state") or {}
        prog_blk = extraction.get("progress") or {}

        scene_out: dict[str, Any] = scene_blk.get("output") or {}
        state_out: dict[str, Any] = state_blk.get("output") or {}
        prog_out: dict[str, Any] = prog_blk.get("output") or {}

        raw_streams: dict[str, dict[str, Any]] = {}
        for s in ("scene", "state", "progress"):
            sev = extraction.get(s) or {}
            raw_streams[s] = {
                "ms": sev.get("ms"),
                "tokens_in": sev.get("tokens_in"),
                "tokens_out": sev.get("tokens_out"),
                "skipped": bool(sev.get("skipped", False)),
                "error": sev.get("error"),
                "attempts": int(sev.get("attempts") or 1),
                "retry_errors": sev.get("retry_errors") or [],
            }

        streams: dict[str, dict[str, Any]] = {}

        r_in = rules_ev_d.get("tokens_in")
        r_out = rules_ev_d.get("tokens_out")
        r_ms = rules_ev_d.get("total_ms")
        rules_status = _tv_rules_status(rules_ev_d)

        streams["rules"] = {
            "tt": _fmt_ms(r_ms),
            "tokens_in": r_in,
            "tokens_out": r_out,
            "tokens_in_display": _fmt_tokens_exact(r_in),
            "tokens_out_display": _fmt_tokens_exact(r_out),
            "skipped": False,
            "error": None,
            "attempts": 1,
            "status": rules_status,
            "status_class": _STATUS_CSS.get(rules_status, "tv-sts-ok"),
            "stage_class": _STAGE_CSS["rules"],
        }

        n_in = narr.get("tokens_in")
        n_out = narr.get("tokens_out")
        n_ms = narr.get("total_ms")
        streams["narrate"] = {
            "tt": _fmt_ms(n_ms),
            "tokens_in": n_in,
            "tokens_out": n_out,
            "tokens_in_display": _fmt_tokens_exact(n_in),
            "tokens_out_display": _fmt_tokens_exact(n_out),
            "skipped": False,
            "error": None,
            "attempts": 1,
            "status": "ok",
            "status_class": _STATUS_CSS["ok"],
            "stage_class": _STAGE_CSS["narrate"],
        }

        for key in ("scene", "state", "progress"):
            s_data = raw_streams[key]
            s_in = s_data["tokens_in"]
            s_out = s_data["tokens_out"]
            s_ms = s_data["ms"]
            s_skip = s_data["skipped"]
            err = s_data.get("error")
            err_s = str(err) if err else None
            attempts = int(s_data.get("attempts") or 1)
            st = _tv_extract_stream_status(
                key,
                skipped=s_skip,
                error=err_s,
                attempts=attempts,
                rejected=rej if isinstance(rej, list) else [],
            )
            streams[key] = {
                "tt": "\u2014" if s_skip else _fmt_ms(s_ms),
                "tokens_in": s_in,
                "tokens_out": s_out,
                "tokens_in_display": "\u2014" if s_skip else _fmt_tokens_exact(s_in),
                "tokens_out_display": "\u2014" if s_skip else _fmt_tokens_exact(s_out),
                "skipped": s_skip,
                "error": err_s,
                "attempts": attempts,
                "retry_errors": s_data.get("retry_errors") or [],
                "status": st,
                "status_class": _STATUS_CSS.get(st, "tv-sts-ok"),
                "stage_class": _STAGE_CSS[key],
            }

        token_sums: list[int] = []
        for stg in ("rules", "narrate", "scene", "state", "progress"):
            tin = streams[stg].get("tokens_in") or 0
            tout = streams[stg].get("tokens_out") or 0
            sm = int(tin) + int(tout)
            token_sums.append(sm)
            streams[stg]["token_sum"] = sm
        max_sum = max(token_sums) if token_sums else 1
        if max_sum < 1:
            max_sum = 1
        for stg in ("rules", "narrate", "scene", "state", "progress"):
            sm = int(streams[stg]["token_sum"])
            streams[stg]["token_bar_pct"] = round(100.0 * sm / float(max_sum), 1)

        total_in = (
            (r_in or 0)
            + (n_in or 0)
            + (raw_streams["scene"]["tokens_in"] or 0)
            + (raw_streams["state"]["tokens_in"] or 0)
            + (raw_streams["progress"]["tokens_in"] or 0)
        )
        total_out = (
            (r_out or 0)
            + (n_out or 0)
            + (raw_streams["scene"]["tokens_out"] or 0)
            + (raw_streams["state"]["tokens_out"] or 0)
            + (raw_streams["progress"]["tokens_out"] or 0)
        )
        total_tt_ms = (r_ms or 0) + (n_ms or 0) + (ext.get("total_ms") or 0)

        narr_text = str(narr_prompt.get("output") or "")
        connectors: list[dict[str, Any]] = []

        def _rules_seg(target: str) -> dict[str, Any]:
            return {
                "from": "rules",
                "label": f"rules \u2192 {target}",
                "lines": _tv_dict_to_lines(
                    rules_ev_d,
                    skip_keys=("tokens_in", "tokens_out", "total_ms"),
                ),
                "anchor": "rules",
                "upstream_status": streams["rules"]["status"],
                "upstream_status_class": streams["rules"]["status_class"],
            }

        if rules_ev_d:
            connectors.append(
                {
                    "before_stage": "narrate",
                    "segments": [
                        {
                            "from": "rules",
                            "label": "rules \u2192 narrate",
                            "lines": _tv_dict_to_lines(
                                rules_ev_d,
                                skip_keys=("tokens_in", "tokens_out", "total_ms"),
                            ),
                            "anchor": "rules",
                            "upstream_status": streams["rules"]["status"],
                            "upstream_status_class": streams["rules"]["status_class"],
                        }
                    ],
                }
            )
        scene_segments: list[dict[str, Any]] = [
            {
                "from": "narrate",
                "label": "narrate \u2192 scene",
                "lines": _tv_narration_lines(narr_text),
                "anchor": "narrate",
                "upstream_status": streams["narrate"]["status"],
                "upstream_status_class": streams["narrate"]["status_class"],
            }
        ]
        if rules_ev_d:
            scene_segments.insert(0, _rules_seg("scene"))
        connectors.append({"before_stage": "scene", "segments": scene_segments})

        state_segments: list[dict[str, Any]] = [
            {
                "from": "narrate",
                "label": "narrate \u2192 state",
                "lines": _tv_narration_lines(narr_text),
                "anchor": "narrate",
                "upstream_status": streams["narrate"]["status"],
                "upstream_status_class": streams["narrate"]["status_class"],
            },
            {
                "from": "scene",
                "label": "scene \u2192 state",
                "lines": _tv_dict_to_lines(scene_out),
                "anchor": "scene",
                "upstream_status": streams["scene"]["status"],
                "upstream_status_class": streams["scene"]["status_class"],
            },
        ]
        if rules_ev_d:
            state_segments.insert(0, _rules_seg("state"))
        connectors.append({"before_stage": "state", "segments": state_segments})

        progress_segments: list[dict[str, Any]] = [
            {
                "from": "narrate",
                "label": "narrate \u2192 progress",
                "lines": _tv_narration_lines(narr_text),
                "anchor": "narrate",
                "upstream_status": streams["narrate"]["status"],
                "upstream_status_class": streams["narrate"]["status_class"],
            },
            {
                "from": "scene",
                "label": "scene \u2192 progress",
                "lines": _tv_dict_to_lines(scene_out),
                "anchor": "scene",
                "upstream_status": streams["scene"]["status"],
                "upstream_status_class": streams["scene"]["status_class"],
            },
            {
                "from": "state",
                "label": "state \u2192 progress",
                "lines": _tv_dict_to_lines(state_out),
                "anchor": "state",
                "upstream_status": streams["state"]["status"],
                "upstream_status_class": streams["state"]["status_class"],
            },
        ]
        if rules_ev_d:
            progress_segments.insert(0, _rules_seg("progress"))
        connectors.append({"before_stage": "progress", "segments": progress_segments})

        state_rej = [
            r
            for r in (rej if isinstance(rej, list) else [])
            if isinstance(r, dict) and r.get("field") == "inventory_remove"
        ]
        has_retries = any(
            int((extraction.get(s) or {}).get("attempts") or 1) > 1
            for s in ("scene", "state", "progress")
        )
        has_errors = any(
            bool(streams[s].get("error"))
            for s in ("scene", "state", "progress")
        )
        has_skipped = any(
            streams[s].get("skipped")
            for s in ("scene", "state", "progress")
        )

        rules_intent = _tv_parse_json_blob(rules_prompt.get("output"))

        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid[:8] if len(tid) >= 8 else tid,
                "trace_id_full": tid,
                "has_rejections": bool(rej),
                "has_retries": has_retries,
                "has_errors": has_errors,
                "has_skipped": has_skipped,
                "streams": streams,
                "connectors": connectors,
                "rules_event": rules_ev_d,
                "rules_intent": rules_intent,
                "state_rejections": state_rej,
                "total_tt": _fmt_ms(total_tt_ms),
                "total_tokens_in": total_in,
                "total_tokens_out": total_out,
                "total_tokens_in_display": _fmt_tokens_exact(total_in),
                "total_tokens_out_display": _fmt_tokens_exact(total_out),
                "user_input": ev.get("input", ""),
                "rules_prompt": {
                    "system": rules_prompt.get("rendered_system", ""),
                    "user": rules_prompt.get("rendered_user", ""),
                    "output": rules_prompt.get("output", ""),
                },
                "narrate_prompt": {
                    "system": narr_prompt.get("rendered_system", ""),
                    "user": narr_prompt.get("rendered_user", ""),
                    "output": narr_text,
                },
                "scene_prompt": {
                    "system": extraction.get("scene", {}).get("rendered_system", ""),
                    "user": extraction.get("scene", {}).get("rendered_user", ""),
                    "output": json.dumps(scene_out, indent=2)
                    if extraction.get("scene")
                    and not extraction.get("scene", {}).get("skipped", False)
                    else "",
                },
                "state_prompt": {
                    "system": extraction.get("state", {}).get("rendered_system", ""),
                    "user": extraction.get("state", {}).get("rendered_user", ""),
                    "output": json.dumps(state_out, indent=2)
                    if extraction.get("state")
                    and not extraction.get("state", {}).get("skipped", False)
                    else "",
                },
                "progress_prompt": {
                    "system": extraction.get("progress", {}).get("rendered_system", ""),
                    "user": extraction.get("progress", {}).get("rendered_user", ""),
                    "output": json.dumps(prog_out, indent=2)
                    if extraction.get("progress")
                    and not extraction.get("progress", {}).get("skipped", False)
                    else "",
                },
            }
        )
    rows.reverse()
    return rows, False
