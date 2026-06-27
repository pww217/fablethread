from __future__ import annotations

import json
import re
from typing import Any

from ccya.ev.events import (
    STREAMS,
    _build_state_diff,
    _get_nested,
    _has_errors,
    _has_rejections,
    _has_retries,
    _parse_ruling_intent,
    _stream_keys,
    _total_tt,
    _total_tokens_in,
    _total_tokens_out,
    _try_parse_json,
    extract_extraction_context,
)
from ccya.ev.inspect import extract_prompt
from ccya.ev.output import _dict_to_lines, extract_section_by_pattern

ARROW = "\u2192"
EM_DASH = "\u2014"
HLINE = "\u2500"


def _extract_connectors(ev: dict[str, Any]) -> list[dict[str, Any]]:
    connectors = []
    stream_inputs = {
        "ruling": [],
        "narrate": ["ruling"],
        "scene": ["ruling", "narrate"],
        "state": ["ruling", "narrate", "scene"],
        "storytell": ["ruling", "narrate", "scene", "state"],
    }
    is_text = {"narrate": True}

    for sd in STREAMS:
        inputs = stream_inputs.get(sd, [])
        if not inputs:
            continue
        segments = []
        for inp_key in inputs:
            inp_path = "narrate_prompt" if inp_key == "narrate" else ("ruling_prompt" if inp_key == "ruling" else f"extraction.{inp_key}")
            inp_blob = _get_nested(ev, inp_path) or {}
            if not isinstance(inp_blob, dict):
                inp_blob = {}
            raw_out = inp_blob.get("output")

            if is_text.get(inp_key):
                seg_lines = [{"k": "chars", "v": str(len(str(raw_out or ""))), "dim": not raw_out},
                             {"k": "text", "v": str(raw_out or "")[:150], "dim": False}]
            else:
                parsed = _try_parse_json(raw_out) if isinstance(raw_out, str) else (raw_out if isinstance(raw_out, dict) else None)
                if parsed and isinstance(parsed, dict):
                    seg_lines = _dict_to_lines(parsed)
                elif parsed:
                    seg_lines = [{"k": "_", "v": str(parsed), "dim": False}]
                else:
                    seg_lines = [{"k": "_", "v": str(raw_out or ""), "dim": False}] if raw_out else []

            segments.append({
                "from": inp_key,
                "label": f"{inp_key} {ARROW} {sd}",
                "lines": seg_lines,
                "anchor": inp_key,
            })
        connectors.append({"before_stage": sd, "segments": segments})
    return connectors


def cmd_deltas(ev: dict[str, Any], events: list[dict[str, Any]] | None = None, compact: bool = False) -> None:
    if compact:
        _cmd_deltas_compact(ev, events)
    else:
        _cmd_deltas_full(ev, events)


def _cmd_deltas_full(ev: dict[str, Any], events: list[dict[str, Any]] | None = None) -> None:
    turn_num = ev.get("turn", "?")
    print(f"=== Turn {turn_num} {EM_DASH} State Deltas ===\n")

    state_diff = ev.get("state_diff") or _build_state_diff(ev)
    for entry in state_diff:
        if isinstance(entry, dict):
            print(f"[{entry.get('from_stream', '?')}] {entry.get('domain', '')}.{entry.get('field', '')} = {entry.get('value', '')}")
        else:
            print(entry)
    print()

    print("--- Extraction Context ---")
    ctx = extract_extraction_context(ev)
    if ctx:
        for k, v in ctx.items():
            if v:
                print(f"  {k}: {v}")
            else:
                print(f"  {k}: (empty)")
    else:
        print("  (none)")
    print()

    print("--- Sanitizer ---")
    if events:
        sanitizer_events = [e for e in events if e.get("kind") == "sanitizer" and e.get("turn") == ev.get("turn")]
        if sanitizer_events:
            for se in sanitizer_events:
                for field in ("threads_updated", "threads_added", "threads_resolved", "goal_changed"):
                    val = se.get(field)
                    if val:
                        print(f"  {field}: {val}")
        else:
            print("  (no sanitizer run)")
    else:
        print("  (no sanitizer run)")
    print()

    print("--- Rejections ---")
    rejections = ev.get("rejected") or []
    if rejections:
        for r in rejections:
            if isinstance(r, dict):
                print(f"  {r.get('field', '?')}: {r.get('reason', '')}")
    else:
        print("  (none)")


def _cmd_deltas_compact(ev: dict[str, Any], events: list[dict[str, Any]] | None = None) -> None:
    """Compact delta view showing only thread/inventory/condition/gm_beat changes."""
    turn_num = ev.get("turn", "?")

    print(f"=== Turn {turn_num} {EM_DASH} Deltas (compact) ===\n")

    # Threads from sanitizer
    threads = []
    if events:
        sanitizer_events = [e for e in events if e.get("kind") == "sanitizer" and e.get("turn") == ev.get("turn")]
        for se in sanitizer_events:
            for tid in (se.get("threads_updated") or []):
                threads.append(f"+{tid}")
            for tid in (se.get("threads_added") or []):
                threads.append(f"++{tid}")
            for tid in (se.get("threads_resolved") or []):
                threads.append(f"--{tid}")

    # Inventory changes from applied
    inventory = []
    applied = ev.get("applied") or {}
    for item in (applied.get("inventory_add") or []):
        if isinstance(item, dict):
            inventory.append(f"+{item.get('id', '?')}")
    for item in (applied.get("inventory_remove") or []):
        if isinstance(item, dict):
            inventory.append(f"-{item.get('id', '?')}")

    # Condition changes from applied
    conditions = []
    for item in (applied.get("pc_condition_add") or []):
        if isinstance(item, dict):
            conditions.append(f"+{item.get('id', '?')}")
    for item in (applied.get("pc_condition_remove") or []):
        if isinstance(item, dict):
            conditions.append(f"-{item.get('id', '?')}")

    # GM Beat from state.meta.pending_gm_beat (moved from record extraction)
    gm_beat = ""
    last_state = ev.get("last_turn_state") or {}
    meta = last_state.get("meta") or {}
    pending_gm = meta.get("pending_gm_beat") or {}
    if isinstance(pending_gm, dict) and pending_gm.get("type"):
        gm_beat = f"beat:{pending_gm.get('type', '')}/{pending_gm.get('effect', '')}"

    # Print compact table
    has_data = threads or inventory or conditions or gm_beat or ev.get("rejected")

    if not has_data:
        print("  (no notable changes)")
    else:
        if threads:
            print(f"  Threads: {', '.join(threads)}")
        if inventory:
            print(f"  Inventory: {', '.join(inventory)}")
        if conditions:
            print(f"  Conditions: {', '.join(conditions)}")
        if gm_beat:
            print(f"  GM Beat: {gm_beat}")
        if ev.get("rejected"):
            print(f"  Rejected: {len(ev['rejected'])} field(s)")

    # Band
    ruling = ev.get("ruling") or {}
    if ruling.get("band"):
        print(f"  Band: {ruling['band']}")


def cmd_mechanics(
    ev: dict[str, Any],
    events: list[dict[str, Any]] | None = None,
    show_pacing: bool = False,
    show_dice: bool = False,
    show_sanitize: bool = False,
) -> None:
    turn_num = ev.get("turn", "?")
    print(f"=== Turn {turn_num} {EM_DASH} Mechanics ===\n")

    if show_pacing:
        _show_pacing(ev)
        return

    if show_dice and events is not None:
        _show_dice(events)
        return

    if show_sanitize and events is not None:
        _show_sanitizer(events)
        return

    print("--- Rules Intent ---")
    intent = _parse_ruling_intent(ev)
    print(json.dumps(intent, indent=2) if intent else "(none)")
    print()

    storytell_event = extract_prompt(ev, "storytell")["user"]
    narrate_user = extract_prompt(ev, "narrate")["user"]

    print("--- GM Beat ---")
    pending_beat_match = re.search(r"\*\*Beat type:\*\*\s*(.+)", narrate_user) if narrate_user else None
    if pending_beat_match:
        print(f"  Pending (to narrate): {pending_beat_match.group(1)}")
    else:
        print("  Pending (to narrate): (none)")
    storytell_output_raw = extract_prompt(ev, "storytell")["output"]
    generated_beat = None
    if storytell_output_raw:
        try:
            so = json.loads(storytell_output_raw)
            generated_beat = so.get("gm_beat")
        except (json.JSONDecodeError, TypeError):
            pass
    if generated_beat:
        print("  Generated (stored):", generated_beat)
    else:
        print("  Generated (stored): (none)")
    print()

    print("--- Rules Outcome ---")
    rules = extract_section_by_pattern(storytell_event, "rules_outcome", "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    if not rules:
        band_match = re.search(r"\*\*Band:\*\*\s*(.+?)(?:\s*" + ARROW + r"|$)", narrate_user) if narrate_user else None
        if band_match:
            rules = band_match.group(0)
    print(rules if rules else "(empty)")
    print()

    print("--- Pacing Context ---")
    pacing = extract_section_by_pattern(storytell_event, "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    print(pacing if pacing else "(empty)")
    print()

    print("--- Active Threads (from storytell) ---")
    threads = extract_section_by_pattern(storytell_event, "threads", "recent_events", "inventory", "rules_outcome", "pacing_context", "last_turn_narration", "player_intent", "current_narration")
    if threads:
        for line in threads.splitlines():
            print(f"  {line.strip()}")
    else:
        print("  (none)")
    print()

    print("--- Campaign Arc (from narrate) ---")
    narrate_user = extract_prompt(ev, "narrate")["user"]
    arc = extract_section_by_pattern(narrate_user, "campaign_arc")
    print(arc if arc else "(empty)")
    print()

    print("--- Narrative (player received) ---")
    narrate_output = extract_prompt(ev, "narrate")["output"]
    if narrate_output and len(narrate_output) > 500:
        print(narrate_output[:500])
        print("\u2026")
    elif narrate_output:
        print(narrate_output)
    else:
        print("(empty)")
    print()

    print("--- State Deltas ---")
    state_diff = ev.get("state_diff") or _build_state_diff(ev)
    if state_diff:
        for entry in state_diff:
            if isinstance(entry, dict):
                print(f"  [{entry.get('from_stream', '?')}] {entry.get('domain', '')}.{entry.get('field', '')} = {entry.get('value', '')}")
            else:
                print(f"  {entry}")
    else:
        print("  (none)")
    print()

    print("--- Connectors ---")
    connectors = _extract_connectors(ev)
    if connectors:
        for conn in connectors:
            print(f"before_stage: {conn.get('before_stage', '?')}")
            for seg in conn.get("segments", []):
                print(f"  from={seg.get('from', '?')} label={seg.get('label', '')}")
                for line in seg.get("lines", []):
                    if isinstance(line, dict):
                        print(f"    {line.get('k', '?')} = {line.get('v', '')}")
                    else:
                        print(f"    {line}")
    else:
        print("  (none)")
    print()

    print("--- Summary ---")
    total_tt = _total_tt(ev)
    total_in = _total_tokens_in(ev)
    total_out = _total_tokens_out(ev)
    has_retries = _has_retries(ev)
    has_errors = _has_errors(ev)
    has_rejections = _has_rejections(ev)
    print(
        f"  streams: {_stream_keys(ev)} "
        f"has_rejections: {has_rejections} "
        f"has_retries: {has_retries} "
        f"has_errors: {has_errors} "
        f"total_tt: {total_tt} "
        f"tokens_in: {total_in} "
        f"tokens_out: {total_out}"
    )


def _show_pacing(ev: dict[str, Any]) -> None:
    print(f"=== Turn {ev.get('turn', '?')} \u2014 Pacing Context ===\n")
    pacing_ctx = ev.get("pacing_context") or {}

    scene_phase = pacing_ctx.get("scene_phase", "SETUP")
    climax_count = pacing_ctx.get("climax_turn_count", 0)
    breather_count = pacing_ctx.get("breather_turn_count", 0)
    convergence = pacing_ctx.get("convergence_score", 0)
    print(f"  scene_phase: {scene_phase}  climax_turn_count={climax_count}  breather_turn_count={breather_count}  convergence_score={convergence}")

    summary = pacing_ctx.get("summary", "")
    print(f"  summary: {summary}" if summary else "  summary: (none)")

    outcome_hint = pacing_ctx.get("outcome_hint")
    if outcome_hint:
        print(f"  outcome_hint: {outcome_hint}")

    result = ev.get("ruling") or {}

    band_label = result.get("band", "")
    if band_label:
        print(f"  band: {band_label}")

    if result.get("impossible"):
        print(f"  impossible: true \u2014 {result.get('reason', '')}")


def _show_dice(events: list[dict[str, Any]]) -> None:
    rows: list[dict[str, Any]] = []
    band_counts: dict[str, int] = {}
    skill_counts: dict[str, int] = {}
    total_rolls = 0

    for ev in events:
        ruling = ev.get("ruling") or {}
        if not ruling.get("rolled"):
            continue
        skill = ruling.get("skill", "?")
        difficulty = ruling.get("difficulty", "?")
        dice = ruling.get("dice", [])
        raw_total = ruling.get("raw_total")
        final_total = ruling.get("final_total", "?")
        band = ruling.get("band", "?")
        stat_mod = ruling.get("stat_mod", 0)
        diff_mod = ruling.get("diff_mod", 0)

        if raw_total is None and isinstance(dice, list):
            raw_total = sum(dice) + (stat_mod or 0) + (diff_mod or 0)

        rows.append({
            "turn": ev.get("turn", "?"),
            "skill": skill,
            "difficulty": difficulty,
            "dice": dice if isinstance(dice, list) else [],
            "raw_total": raw_total,
            "final_total": final_total,
            "band": band,
            "stat_mod": stat_mod or 0,
            "diff_mod": diff_mod or 0,
        })
        total_rolls += 1
        band_counts[str(band)] = band_counts.get(str(band), 0) + 1
        key = str(skill)
        skill_counts[key] = skill_counts.get(key, 0) + 1

    if not rows:
        print("(no dice rolls found)")
        return

    ARROW = "\u2192"
    HLINE = "\u2500"
    header = f"{'Turn':>4} | {'Skill':<12} | {'Difficulty':<12} | {'Dice':<12} | {'Raw ' + ARROW + ' Final':<14} | {'Band':<14} | {'Modifiers'}"
    sep = HLINE * len(header)
    print(header)
    print(sep)
    for r in rows:
        dice_raw = r.get("dice", [])
        if len(dice_raw) == 1:
            dice_str = f"d12:{dice_raw[0]}"
        elif dice_raw:
            dice_str = str(dice_raw)
        else:
            dice_str = "[]"
        raw_s = str(r["raw_total"]) if r["raw_total"] is not None else "?"
        final_s = str(r["final_total"]) if r["final_total"] is not None else "?"
        mods = f"stat:{r['stat_mod']:+d} diff:{r['diff_mod']:+d}"
        print(
            f"{r['turn']:>4} | {str(r['skill']):<12} | {str(r['difficulty']):<12} | {dice_str:<12} | {raw_s} \u2192 {final_s:<9} | {str(r['band']):<14} | {mods}"
        )

    print()
    print(f"Total rolls: {total_rolls}")
    print(f"Band distribution: {', '.join(f'{k}={v}' for k, v in sorted(band_counts.items()))}")
    print(f"Skills used: {', '.join(f'{k}={v}' for k, v in sorted(skill_counts.items()))}")


def _show_sanitizer(events: list[dict[str, Any]]) -> None:
    print("=== Sanitizer Events ===\n")
    sanitizer_events = [e for e in events if e.get("kind") == "sanitizer"]
    if not sanitizer_events:
        print("(no sanitizer events found)")
        return
    for se in sanitizer_events:
        turn = se.get("turn", "?")
        print(f"Turn {turn}:")
        for field in ("threads_updated", "threads_removed", "threads_resolved", "threads_added", "goal_changed"):
            val = se.get(field)
            if val:
                print(f"  {field}: {val}")
        cd = se.get("changes_detail")
        if cd:
            print(f"  changes_detail: {cd}")
        print()
