"""Turn viewer data preparation and _tv_* helpers."""

from __future__ import annotations

import json as _json
import logging
from pathlib import Path
from typing import Any

from ccya.state import load_state
from .metrics import _fmt_tokens_exact
from .tv_mirror import _STREAMS, STREAM_BY_KEY, _get_nested

_log = logging.getLogger(__name__)

_STATUS_CSS: dict[str, str] = {
    "ok": "tv-sts-ok",
    "skipped": "tv-sts-skipped",
    "retried": "tv-sts-retried",
    "rejected": "tv-sts-rejected",
    "error": "tv-sts-error",
}

_STAGE_CSS: dict[str, str] = {
    "ruling": "tv-stage-ruling",
    "narrate": "tv-stage-narrate",
    "scene": "tv-stage-scene",
    "state": "tv-stage-state",
    "record": "tv-stage-storytell",
    "world": "tv-stage-world",
}


def _get_input_segments(ev: dict[str, Any], sd) -> dict[str, list[dict[str, Any]]]:
    """Return {inp_key: lines} for all inputs of stream definition `sd`."""
    result: dict[str, list[dict[str, Any]]] = {}
    if not sd.inputs:
        return result
    for inp_key in sd.inputs:
        inp_sd = STREAM_BY_KEY.get(inp_key)
        if inp_sd is None:
            continue
        inp_p_path = inp_sd.prompt_path or inp_sd.metrics_path
        inp_p_blob = _get_nested(ev, inp_p_path) or {}
        if not isinstance(inp_p_blob, dict):
            inp_p_blob = {}
        raw_out = inp_p_blob.get(inp_sd.output_subkey) if inp_sd.output_subkey else inp_p_blob
        result[inp_key] = _extract_stream_output_lines(raw_out, inp_sd)
    return result


def _tv_label(x: dict[str, Any]) -> str:
    """Extract a human-readable label from a dict for display purposes."""
    for key in ("id", "name", "text", "label"):
        val = x.get(key)
        if val and isinstance(val, str):
            return val[:60]
    return str(list(x.values())[0])[:60] if x else ""


def _tv_parse_json_blob(raw: Any) -> dict[str, Any] | None:
    if not raw or not isinstance(raw, str):
        return None
    s = raw.strip()
    try:
        out = _json.loads(s)
        return out if isinstance(out, dict) else None
    except _json.JSONDecodeError:
        _log.debug("_tv_parse_json_blob first parse failed, trying substring extraction: preview=%r", s[:80])
        i, j = s.find("{"), s.rfind("}")
        if 0 <= i < j:
            try:
                out = _json.loads(s[i : j + 1])
                return out if isinstance(out, dict) else None
            except _json.JSONDecodeError:
                return None
        return None


def _extract_stream_output_lines(raw_out: Any, inp_sd) -> list[dict[str, Any]]:
    """Extract formatted seg_lines from raw output for a given stream descriptor."""
    if inp_sd.is_text_output:
        return _tv_narration_lines(str(raw_out or ""))
    elif inp_sd.output_is_json_string and isinstance(raw_out, str):
        try:
            parsed = _json.loads(raw_out)
            return _tv_dict_to_lines(parsed) if isinstance(parsed, dict) else [{"k": "_", "v": str(raw_out), "dim": False}]
        except Exception as e:
            _log.warning("_extract_stream_output_lines JSON parse failed: %s", e)
            return [{"k": "_", "v": str(raw_out), "dim": False}]
    elif isinstance(raw_out, dict):
        return _tv_dict_to_lines(raw_out)
    else:
        return [{"k": "_", "v": str(raw_out), "dim": False}] if raw_out else []


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
                labels = [_tv_label(x) for x in v if x]
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


def _tv_state_diff(ev: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Produce pacing_items and state_changes from extraction outputs.

    Pacing/Beats: scene candidates, world output (beat candidates), ruling
    beat selection, convergence, phase, allowed_beat_types, recent_beats.

    State changes: threads, inventory, conditions, NPCs, locations, arc
    operations — non-narrative mutations with reasons.
    """
    rejected_set: set[str] = set()
    for r in (ev.get("rejected") or []):
        if isinstance(r, dict) and r.get("field"):
            rejected_set.add(str(r["field"]))

    pacing_items: list[dict[str, Any]] = []
    changes: list[dict[str, Any]] = []

    # --- Pacing/Beats ---

    # Ruling beat selection
    ruling_event = ev.get("ruling") or {}
    selected_beat_idx = ruling_event.get("selected_beat")
    if selected_beat_idx is not None:
        beat_candidates = (ev.get("last_turn_state") or {}).get("meta") or {}
        beat_candidates = beat_candidates.get("beat_candidates") or []
        if isinstance(selected_beat_idx, int) and 0 <= selected_beat_idx < len(beat_candidates):
            chosen = beat_candidates[selected_beat_idx]
            beat_type = chosen.get("type", "?")
            beat_effect = chosen.get("effect", "")
            pacing_items.append({
                "section": "ruling_beat_selection",
                "label": f"selected_beat: {selected_beat_idx} → {beat_type} / {beat_effect}",
            })
        else:
            pacing_items.append({
                "section": "ruling_beat_selection",
                "label": f"selected_beat: {selected_beat_idx} (no candidates available)",
            })
    else:
        pacing_items.append({
            "section": "ruling_beat_selection",
            "label": "selected_beat: null — no fit",
        })

    # World output — beat candidates generated
    world_output = _get_nested(ev, "extraction.world") or {}
    if isinstance(world_output, dict):
        world_out = world_output.get("output")
        if isinstance(world_out, list) and world_out:
            labels = []
            for i, bc in enumerate(world_out):
                if isinstance(bc, dict):
                    bt = bc.get("type", "?")
                    be = bc.get("effect", "")
                    labels.append(f"[{i}] {bt} / {be}")
                else:
                    labels.append(f"[{i}] {str(bc)[:80]}")
            pacing_items.append({
                "section": "world_beat_candidates",
                "label": f"World — Beat Candidates Generated ({len(labels)})",
                "sublines": labels,
            })

    # Scene candidate_npcs
    scene_output = _get_nested(ev, "extraction.scene") or {}
    if isinstance(scene_output, dict):
        scene_out = scene_output.get("output")
        if isinstance(scene_out, dict):
            cnp = scene_out.get("candidate_npcs")
            if isinstance(cnp, list) and cnp:
                labels = []
                for npc in cnp:
                    if isinstance(npc, dict):
                        name = npc.get("name", npc.get("id", "?"))
                        role = npc.get("role", "")
                        labels.append(f"{name}" + (f" ({role})" if role else ""))
                pacing_items.append({
                    "section": "scene_candidate_npcs",
                    "label": f"Scene — Candidate NPCs ({len(labels)})",
                    "sublines": labels,
                })

    # Recent beats history
    last_state = ev.get("last_turn_state") or {}
    meta = last_state.get("meta") or {}
    recent_beats = meta.get("recent_beats") or []
    if isinstance(recent_beats, list) and recent_beats:
        parts = []
        for rb in recent_beats[-5:]:
            if isinstance(rb, dict):
                turn = rb.get("turn", "?")
                btype = rb.get("type", "?")
                parts.append(f"T{turn}:{btype}")
            else:
                parts.append(str(rb))
        pacing_items.append({
            "section": "recent_beats",
            "label": f"Recent Beats: {', '.join(parts)}",
        })

    # Pacing context extras
    pacing_ctx = ev.get("pacing_context") or {}
    convergence_components = pacing_ctx.get("convergence_components")
    if isinstance(convergence_components, dict) and convergence_components:
        parts = []
        for k, v in convergence_components.items():
            if v:
                parts.append(f"{k}: {v}")
        if parts:
            pacing_items.append({
                "section": "convergence_components",
                "label": f"components: {{{', '.join(parts)}}}",
            })

    allowed_beat_types = ev.get("allowed_beat_types")
    if isinstance(allowed_beat_types, list) and allowed_beat_types:
        pacing_items.append({
            "section": "allowed_beat_types",
            "label": f"allowed_beat_types: [{', '.join(str(x) for x in allowed_beat_types)}]",
        })

    spiral_detected = pacing_ctx.get("spiral_detected")
    if spiral_detected:
        pacing_items.append({
            "section": "spiral_detected",
            "label": "spiral_detected: true",
        })

    # --- State changes (organized by concern) ---

    # Helper: extract parsed output from a stream path
    def _extract_parsed(path: str) -> dict[str, Any] | None:
        blob = _get_nested(ev, path) or {}
        if not isinstance(blob, dict):
            return None
        raw_out = blob.get("output")
        if not raw_out:
            return None
        if isinstance(raw_out, str):
            return _tv_parse_json_blob(raw_out)
        elif isinstance(raw_out, dict):
            return raw_out
        return None

    # Helper: format a value for display
    def _format_value(field_key: str, val: Any, default_op: str = "set") -> tuple[str, str]:
        """Returns (value_str, op) for a field."""
        # For dicts: show field names instead of full JSON
        if isinstance(val, dict):
            keys = list(val.keys())
            if keys:
                return ", ".join(keys), default_op
            return "\u2014", default_op

        # For lists of dicts: show count + union of all keys
        if isinstance(val, list) and val and all(isinstance(x, dict) for x in val):
            all_keys: set[str] = set()
            for item in val:
                all_keys.update(item.keys())
            key_str = ", ".join(sorted(all_keys))
            return f"[{len(val)}] {key_str}", default_op

        # For lists of primitives: show values
        if isinstance(val, list):
            value_str = ", ".join(str(x) for x in val[:4])
            if len(val) > 4:
                value_str += "\u2026"
            return value_str, default_op

        # For strings: truncate
        if isinstance(val, str):
            return val[:120] + ("\u2026" if len(val) > 120 else ""), default_op

        return str(val), default_op

    # 1. Intent (from ruling)
    ruling_intent = _tv_parse_json_blob(ev.get("ruling_prompt", {}).get("output") or "")
    if ruling_intent:
        val = ruling_intent.get("intent")
        if val and isinstance(val, str) and val.strip():
            changes.append({
                "domain": "intent",
                "op": "set",
                "field": "intent",
                "value": val[:120] + ("\u2026" if len(val) > 120 else ""),
                "rejected": False,
                "from_stream": "ruling",
            })

    # 2. Threads (from record)
    record_parsed = _extract_parsed("extraction.record") or {}
    thread_fields = [
        ("thread_update", "set"),
        ("thread_resolve", "set"),
        ("thread_add", None),
    ]
    for field_key, default_op in thread_fields:
        val = record_parsed.get(field_key)
        if val is None:
            continue
        if isinstance(val, list) and not val:
            continue
        if isinstance(val, dict) and not val:
            continue
        value_str, op = _format_value(field_key, val, default_op or "set")
        changes.append({
            "domain": "record",
            "op": op,
            "field": field_key,
            "value": value_str,
            "rejected": field_key in rejected_set,
            "from_stream": "record",
            "concern": "threads",
        })

    # 3. Inventory (from state)
    state_parsed = _extract_parsed("extraction.state") or {}
    inventory_fields = [
        ("inventory_change_reason", None),
        ("inventory_add", "add"),
        ("inventory_remove", "remove"),
        ("inventory_update", "update"),
    ]
    for field_key, default_op in inventory_fields:
        val = state_parsed.get(field_key)
        if val is None:
            continue
        if isinstance(val, list) and not val:
            continue
        if isinstance(val, dict) and not val:
            continue
        # inventory_change_reason: show as reason line
        if field_key == "inventory_change_reason":
            if val and val != "none":
                changes.append({
                    "domain": "state",
                    "op": "=",
                    "field": "inventory_change_reason",
                    "value": str(val)[:120],
                    "rejected": False,
                    "from_stream": "state",
                    "concern": "inventory",
                })
        else:
            value_str, op = _format_value(field_key, val, default_op or "update")
            changes.append({
                "domain": "state",
                "op": op,
                "field": field_key,
                "value": value_str,
                "rejected": field_key in rejected_set,
                "from_stream": "state",
                "op_css_class": "update",
                "concern": "inventory",
            })

    # 4. Conditions (from state)
    condition_fields = [
        ("condition_change_reason", None),
        ("pc_condition_add", "add"),
        ("pc_condition_remove", "remove"),
    ]
    for field_key, default_op in condition_fields:
        val = state_parsed.get(field_key)
        if val is None:
            continue
        if isinstance(val, list) and not val:
            continue
        if isinstance(val, dict) and not val:
            continue
        if field_key == "condition_change_reason":
            if val and val != "none":
                changes.append({
                    "domain": "state",
                    "op": "=",
                    "field": "condition_change_reason",
                    "value": str(val)[:120],
                    "rejected": False,
                    "from_stream": "state",
                    "concern": "conditions",
                })
        else:
            value_str, op = _format_value(field_key, val, default_op or "set")
            changes.append({
                "domain": "state",
                "op": op,
                "field": field_key,
                "value": value_str,
                "rejected": field_key in rejected_set,
                "from_stream": "state",
                "concern": "conditions",
            })

    # 5. Arc (from record)
    arc_resolve = record_parsed.get("arc_resolve")
    if arc_resolve is not None:
        if isinstance(arc_resolve, dict) and not arc_resolve:
            pass
        elif arc_resolve:
            value_str, op = _format_value("arc_resolve", arc_resolve, "set")
            changes.append({
                "domain": "record",
                "op": op,
                "field": "arc_resolve",
                "value": value_str,
                "rejected": False,
                "from_stream": "record",
                "concern": "arc",
            })

    # 6. Location (from state)
    location_change = state_parsed.get("location_change")
    location_description = state_parsed.get("location_description")
    if location_change and isinstance(location_change, dict):
        value_str, op = _format_value("location_change", location_change, "set")
        changes.append({
            "domain": "state",
            "op": op,
            "field": "location_change",
            "value": value_str,
            "rejected": False,
            "from_stream": "state",
            "concern": "location",
        })
    if location_description and location_description != "none":
        changes.append({
            "domain": "state",
            "op": "set",
            "field": "location_description",
            "value": location_description[:120],
            "rejected": False,
            "from_stream": "state",
            "concern": "location",
        })

    # 7. NPCs (from scene/state)
    npc_update_fields = []
    for path in ("extraction.scene", "extraction.state"):
        sp = _extract_parsed(path) or {}
        cnpc = sp.get("compendium_npc_update")
        if cnpc and isinstance(cnpc, list) and cnpc:
            npc_update_fields.extend(cnpc)
    if npc_update_fields:
        value_str, op = _format_value("compendium_npc_update", npc_update_fields, "update")
        changes.append({
            "domain": "scene",
            "op": op,
            "field": "compendium_npc_update",
            "value": value_str,
            "rejected": False,
            "from_stream": "scene",
            "concern": "npcs",
        })
    return pacing_items, changes


def _tv_failures(
    ev: dict[str, Any],
    streams: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Collect all failure signals from a turn event into a flat list."""
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
        _log.debug("_turn_viewer_data path=%s not found", path)
        return [], True

    # Read server_errors.jsonl for unified timeline
    server_rows: list[dict[str, Any]] = []
    errors_file = save_dir / "server_errors.jsonl"
    if errors_file.exists():
        raw_errs = errors_file.read_text().strip()
        if raw_errs:
            for line in (ln for ln in raw_errs.splitlines() if ln.strip()):
                try:
                    ev = _json.loads(line)
                except _json.JSONDecodeError as e:
                    _log.warning("Skipping malformed server_errors.jsonl line: %s", e)
                    continue
                entry = dict(ev)
                entry["row_kind"] = "server_error"
                server_rows.append(entry)

    # Existing logic: parse events.jsonl for turn-level events
    raw = path.read_text().strip() or ""
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    rows: list[dict[str, Any]] = []
    for line in lines:
        try:
            ev = _json.loads(line)
        except _json.JSONDecodeError as e:
            _log.warning("Skipping malformed events.jsonl line: %s", e)
            continue

        if ev.get("kind") == "sanitizer":
            chg = ev.get("changes_detail") or {}
            san_diffs: list[dict[str, Any]] = []
            for _tid, _delta in (chg.get("updated") or {}).items():
                for _f in _delta.get("fields") or []:
                    san_diffs.append({
                        "op": "update",
                        "op_sym": "~",
                        "field": f"{_tid}.{_f['field']}",
                        "value": f"{_f['before']} → {_f['after']}",
                    })
                if _delta.get("progress"):
                    pd = _delta["progress"]
                    old_str = "[" + ", ".join(str(p) for p in pd["before"]) + "]"
                    new_str = "[" + ", ".join(str(p) for p in pd["after"]) + "]"
                    san_diffs.append({"op": "remove", "op_sym": "-", "field": f"{_tid}.major_updates", "value": old_str})
                    san_diffs.append({"op": "add", "op_sym": "+", "field": f"{_tid}.major_updates", "value": new_str})
            for _r in chg.get("removed") or []:
                san_diffs.append({"op": "remove", "op_sym": "-", "field": _r["id"], "value": _r.get("reason", "")})
            for _r in chg.get("resolved") or []:
                san_diffs.append({"op": "update", "op_sym": "~", "field": _r["id"], "value": f"[{_r.get('resolution_state', 'resolved')}] {_r.get('outcome', '')}"})
            for _a in chg.get("added") or []:
                san_diffs.append({"op": "add", "op_sym": "+", "field": _a.get("id", ""), "value": f"[{_a.get('urgency', 'normal')}] {_a.get('summary', '')}"})
            goal = chg.get("goal") or {}
            if goal.get("before") != goal.get("after"):
                san_diffs.append({"op": "update", "op_sym": "~", "field": "long_term_objective", "value": f"{goal.get('before', '')} → {goal.get('after', '')}"})

            rows.append({
                "row_kind": "sanitizer",
                "turn": int(ev.get("turn") or 0),
                "ms": round(float(ev.get("ms", 0)), 1),
                "tokens_in": int(ev.get("tokens_in", 0)),
                "tokens_out": int(ev.get("tokens_out", 0)),
                "san_diffs": san_diffs,
                "has_changes": bool(san_diffs),
            })
            continue

        def _fmt_ms(ms: Any) -> str:
            if ms is None:
                return "\u2014"
            try:
                return f"{float(ms) / 1000.0:.1f}s"
            except (TypeError, ValueError):
                _log.debug("_fmt_ms non-numeric value: %r", ms)
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
            
            # Extract output from prompt_path
            prompt_blob = _get_nested(ev, sd.prompt_path) if sd.prompt_path else None
            if prompt_blob and isinstance(prompt_blob, dict):
                output = prompt_blob.get(sd.output_subkey) if sd.output_subkey else prompt_blob
            else:
                output = None
            
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
                "ms_raw": int(ms_val) if ms_val is not None else 0,
                "output": output,
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
        # total_tt: ruling.total_ms + narrate.total_ms + extract.total_ms
        ruling_ev = ev.get("ruling") or {}
        narr_ev = ev.get("narrate") or {}
        extract_ev = ev.get("extract") or {}
        total_tt_ms = (
            (ruling_ev.get("total_ms") or 0)
            + (narr_ev.get("total_ms") or 0)
            + (extract_ev.get("total_ms") or 0)
        )

        # Step 2.4: Connector generation from sd.inputs
        connectors: list[dict[str, Any]] = []
        for sd in _STREAMS:
            if not sd.inputs:
                continue
            segments: list[dict[str, Any]] = []
            input_segments = _get_input_segments(ev, sd)
            for inp_key, seg_lines in input_segments.items():
                segments.append({
                    "from": inp_key,
                    "label": f"{inp_key} \u2192 {sd.key}",
                    "lines": seg_lines,
                    "anchor": inp_key,
                    "upstream_status": streams[inp_key]["status"],
                    "upstream_status_class": streams[inp_key]["status_class"],
                })
            connectors.append({"before_stage": sd.key, "segments": segments})

        # Per-stream inputs snapshot
        inputs_snapshot: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for sd in _STREAMS:
            if not sd.inputs:
                continue
            inputs_snapshot[sd.key] = _get_input_segments(ev, sd)

        # Derived flags from failures list
        row_failures = _tv_failures(ev, streams)
        has_retries = any(f["kind"] == "retry" for f in row_failures)
        has_errors = any(f["kind"] in ("llm_error", "top_level_error") for f in row_failures)
        has_rejections = any(f["kind"] == "rejection" for f in row_failures)
        has_skipped = any(streams[sd.key].get("skipped") for sd in _STREAMS)

        # Pacing items + state diff
        pacing_items, state_diff = _tv_state_diff(ev)

        # Pacing context from event data
        pacing_ctx = ev.get("pacing_context") or {}
        band_label = (ev.get("ruling") or {}).get("band", "")

        # Top-level pacing fields written by turn.py
        convergence_score = ev.get("convergence_score")

        # ruling_intent for template (parsed from ruling_prompt.output)
        ruling_intent = _tv_parse_json_blob((ev.get("ruling_prompt") or {}).get("output"))

        tid = str(ev.get("trace_id") or "")
        tid_short = tid[:8] if len(tid) >= 8 else tid

        rows.append(
            {
                "turn": ev.get("turn", 0),
                "trace_id": tid_short,
                "trace_id_full": tid,
                "has_rejections": has_rejections,
                "has_retries": has_retries,
                "has_errors": has_errors,
                "has_skipped": has_skipped,
                "streams": streams,
                "connectors": connectors,
                "total_tt": _fmt_ms(total_tt_ms),
                "total_tt_ms_raw": int(total_tt_ms),
                "total_tokens_in": total_in,
                "total_tokens_out": total_out,
                "total_tokens_in_display": _fmt_tokens_exact(total_in),
                "total_tokens_out_display": _fmt_tokens_exact(total_out),
                "user_input": ev.get("input", ""),
                "ruling_intent": ruling_intent,
                "pacing_context": {
                    "directive": pacing_ctx.get("directive"),
                    "outcome_hint": pacing_ctx.get("outcome_hint"),
                    "summary": pacing_ctx.get("summary", ""),
                    "scene_phase": pacing_ctx.get("scene_phase"),
                    "climax_turn_count": pacing_ctx.get("climax_turn_count"),
                    "breather_turn_count": pacing_ctx.get("breather_turn_count"),
                    "convergence_score": convergence_score,
                },
                "band_label": band_label,
                "inputs_snapshot": inputs_snapshot,
                "pacing_items": pacing_items,
                "state_diff": state_diff,
                "failures": row_failures,
                "row_kind": "turn",
            }
        )
    rows.reverse()

    # Merge server errors into unified timeline sorted by timestamp
    if server_rows:
        rows.extend(server_rows)
        rows.sort(key=lambda e: e.get("ts", ""))

    # Build seed row from state.yaml if game has been seeded
    no_events = False
    try:
        st = load_state(save_dir)
        meta = st.get("meta", {}) or {}
        if meta.get("_pack_source"):
            seed_state = {
                "pc": st.get("pc"),
                "location": st.get("location"),
                "inventory": st.get("inventory"),
                "scene": st.get("scene"),
                "compendium": st.get("compendium"),
                "arc": st.get("arc"),
            }
            seed_row = {
                "row_kind": "seed",
                "turn": 0,
                "pack_source": meta.get("_pack_source", ""),
                "seed_json": _json.dumps(seed_state, indent=2, default=str),
            }
            __seed_pools = st.get("__seed_pools__") or {}
            if __seed_pools:
                seed_row["seed_pools_json"] = _json.dumps(
                    __seed_pools,
                    indent=2,
                    default=str,
                )
            rows.append(seed_row)
    except Exception as exc:
        _log.warning("Failed to load state for turn_viewer seed display", extra={"error": str(exc)})

    _log.debug("_turn_viewer_data events=%d server_errors=%d", len(rows), len(server_rows))
    return rows, no_events
