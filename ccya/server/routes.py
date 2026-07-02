"""All HTMX route handlers (@app.get / @app.post)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from sse_starlette.sse import EventSourceResponse

from ccya.errors import ErrorKind
from ccya.models import NPCEntry, WorldState
from ccya.engine import (
    format_change_lines,
    narrate_seed,
    prepare_seed,
    run_turn,
)

from ccya.pack import PlayerOverrides, load_pack, list_packs, _resolve_pack_dir
from ccya.state import (
    init_save_dir,
    load_recent_turns,
    load_state,
    remove_last_chronicle_turn,
    remove_last_event,
    save_state,
)
from .panels import (
    _debug_context,
    _get_opening,
    _get_opening_outcome_summary,
    _load_current_state,
    _load_last_actions,
    _load_opening_actions,
    _load_opening_from_chronicle,
    _load_recent_history,
)
from .metrics import _turn_log_entries
from .tv import _turn_viewer_data

# Import the app module to reference its globals (enables test patching)
_app_mod = sys.modules["ccya.server.app"]


def _require_save() -> JSONResponse | None:
    """Return a 400 error if no save is active, or None if save exists."""
    if _app_mod.SAVE_DIR is None:
        return JSONResponse({"error": "No save selected. Switch to a save or create a new game."}, status_code=400)
    return None

_log = logging.getLogger(__name__)


def _generate_save_dir_name(pack_name: str) -> str:
    today = date.today().isoformat()
    safe = pack_name.lower().replace("/", "-").replace(" ", "-")
    safe = "".join(c for c in safe if c.isalnum() or c in "-_")
    return f"{safe}-{today}"


def _apply_seed_to_save_dir(
    seed_dict: dict[str, Any],
    opening_narrative: str | None = None,
    actions: list[str] | None = None,
    *,
    outcome_summary: str = "",
    pack_source: str | None = None,
    pool_selection: dict[str, Any] | None = None,
) -> None:
    """Apply generated seed to a new save directory and set dynamic pack variables."""
    dir_name = _generate_save_dir_name(_app_mod._active_pack.manifest.name)
    save_dir = Path("saves") / dir_name
    _app_mod.SAVE_DIR = save_dir

    seed_dict.setdefault("meta", {})["model"] = _app_mod.engine_config.model
    if pack_source is not None:
        seed_dict.setdefault("meta", {})["_pack_source"] = pack_source
    if opening_narrative is not None:
        seed_dict.setdefault("pc", {}).setdefault("situation", {})["opening"] = opening_narrative
    if opening_narrative is not None or actions is not None:
        seed_dict["seed_meta"] = {
            "actions": actions or [],
            "outcome_summary": outcome_summary,
        }
    init_save_dir(save_dir, WorldState.from_dict(seed_dict))
    if opening_narrative is not None:
        _app_mod._dynamic_opening = opening_narrative
    else:
        _app_mod._dynamic_opening = ""
    _app_mod._dynamic_opening_outcome = outcome_summary


def _format_ts(ts_str: str) -> str:
    """Convert UTC ISO string to a human-readable display string."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b · %I:%M %p UTC").lstrip("0")
    except (ValueError, AttributeError):
        return ts_str  # fallback: return raw if unparseable


def _save_rel_name(save_dir: Path) -> str:
    """Return save directory name relative to saves/ or evals/runs/ for UI display/comparison."""
    for root in [Path("saves"), Path("evals/runs")]:
        try:
            return str(save_dir.resolve().relative_to(root.resolve()))
        except ValueError:
            continue
    return save_dir.name


def _list_saves() -> list[dict[str, Any]]:
    """List all available saves."""
    save_dirs = _app_mod._find_all_save_dirs()
    save_dirs.sort(key=lambda p: p.stat().st_mtime, reverse=True)

    result = []
    for entry in save_dirs:
        name = _save_rel_name(entry)
        events_file = entry / "events.jsonl"

        turn_count = 0
        last_modified: str | None = None
        pack_name: str | None = None
        pc_name: str | None = None
        location_name: str | None = None

        # Try to get turn count from events file
        if events_file.exists():
            try:
                with open(events_file, "r") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                evt = json.loads(line)
                                if evt.get("kind") == "sanitizer":
                                    continue
                                turn_count += 1
                                if evt.get("ts"):
                                    last_modified = evt.get("ts")
                            except json.JSONDecodeError:
                                pass
            except OSError:
                pass

        from ccya.state.io import load_state
        try:
            state = load_state(entry)
        except Exception:
            continue

        pack_name = state.meta.setting_pack
        pc_name = state.pc.name
        location_name = state.location.name

        resolved = entry.resolve()
        kind = "eval" if str(resolved).startswith(str(Path("evals/runs").resolve())) else "user"
        result.append({
            "name": name,
            "display_name": entry.name,
            "pack": pack_name,
            "turn_count": turn_count,
            "last_modified": last_modified,
            "pc_name": pc_name,
            "location_name": location_name,
            "kind": kind,
        })

    return result


@_app_mod.app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if _app_mod.SAVE_DIR is None:
        from ccya.state.io import default_world_state
        ctx = _debug_context()
        ctx["state"] = default_world_state()
        ctx["history"] = []
        ctx["last_actions"] = []
        ctx["opening"] = ""
        ctx["opening_actions"] = []
        ctx["opening_outcome_summary"] = ""
        ctx["has_narrative"] = False
        ctx["pack_name"] = _app_mod._active_pack.manifest.name
        ctx["character_creation_enabled"] = _app_mod.config.get("game", {}).get(
            "character_creation_enabled", True
        )
        ctx["active_save_name"] = ""
        ctx["no_save"] = True
        ctx["last_history_turn"] = None
        css_path = _app_mod.BASE_DIR / "static" / "app.css"
        ctx["css_v"] = int(css_path.stat().st_mtime) if css_path.exists() else 0
        return _app_mod._render("index.html", ctx)
    history = _load_recent_history(_app_mod.SAVE_DIR)
    last_actions = _load_last_actions(_app_mod.SAVE_DIR) if history else []
    state = _load_current_state()
    state = _resolve_npc_ties(state)
    opening = _load_opening_from_chronicle(_app_mod.SAVE_DIR) or _get_opening()
    opening_actions = _load_opening_actions(_app_mod.SAVE_DIR) if not history and not last_actions else []
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    ctx["opening_actions"] = opening_actions
    ctx["opening_outcome_summary"] = _get_opening_outcome_summary() if opening else ""
    ctx["has_narrative"] = bool(opening or history)
    ctx["last_history_turn"] = history[-1].get("turn") if history else None
    ctx["pack_name"] = _app_mod._active_pack.manifest.name
    ctx["character_creation_enabled"] = _app_mod.config.get("game", {}).get(
        "character_creation_enabled", True
    )
    ctx["active_save_name"] = _save_rel_name(_app_mod.SAVE_DIR)
    css_path = _app_mod.BASE_DIR / "static" / "app.css"
    ctx["css_v"] = int(css_path.stat().st_mtime) if css_path.exists() else 0
    return _app_mod._render("index.html", ctx)


@_app_mod.app.get("/turn")
async def get_turn(input: str = ""):
    if err := _require_save():
        return err
    user_input = input.strip()
    if not user_input:

        async def _empty():
            yield {"event": "turn_error", "data": json.dumps({"error": "Empty input"})}

        return EventSourceResponse(_empty())

    if _app_mod._is_turn_in_progress():

        async def _busy():
            yield {
                "event": "turn_error",
                "data": json.dumps({"error": "Turn already in progress"}),
            }

        return EventSourceResponse(_busy())

    async def event_stream():
        try:
            run_turn_generator = run_turn(
                _app_mod.SAVE_DIR,
                user_input,
                config=_app_mod.engine_config,
                template_dir=str(_app_mod.PROMPTS_DIR),
                pack_name_locales=_app_mod._active_pack.scenario.name_locales if _app_mod._active_pack.scenario else _app_mod._active_pack.manifest.name_locales,
                pack_narrator_rules=_app_mod._active_pack.scenario.narrator_rules if _app_mod._active_pack.scenario else [],
                pack_world_rules=_app_mod._active_pack.scenario.world_rules if _app_mod._active_pack.scenario else [],
                pack_factions=[f.model_dump() for f in (_app_mod._active_pack.scenario.factions if _app_mod._active_pack.scenario else [])],
            )
            async for kind, payload in run_turn_generator:
                if kind == "token":
                    yield {
                        "event": "narrative_token",
                        "data": json.dumps({"chunk": payload}),
                    }
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "panel_update":
                    yield {
                        "event": "panel_update",
                        "data": json.dumps(payload),
                    }
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        err_dict = err if isinstance(err, dict) else {"message": str(err)}
                        error_msg = err_dict.get("message", str(err))
                        error_kind = err_dict.get("kind", ErrorKind.TURN_PROCESSING_FAILED)
                        yield {
                            "event": "turn_error",
                            "data": json.dumps({
                                "error": error_msg,
                                "kind": error_kind,
                                "trace_id": result.trace_id,
                            }),
                        }

                    # Check if all 3 extraction streams failed (LLM crash) — don't show success state
                    extract_metrics = result.metrics.get("extract", {}) or {}
                    streams = extract_metrics.get("streams", {}) or {}
                    scene_skipped = (streams.get("scene") or {}).get("skipped", False)
                    state_skipped = (streams.get("state") or {}).get("skipped", False)
                    record_skipped = (streams.get("record") or {}).get("skipped", False)

                    if scene_skipped and state_skipped and record_skipped:
                        yield {
                            "event": "turn_error",
                            "data": json.dumps({
                                "error": f"All extraction streams failed. Trace `{result.trace_id}` — try rephrasing.",
                                "trace_id": result.trace_id,
                            }),
                        }

                    ch = result.changes if isinstance(result.changes, dict) else {}
                    # Format ts field for display (engine stores UTC ISO, UI gets human-readable)
                    _ts_display = _format_ts(result.ts)
                    yield {
                        "event": "turn_complete",
                        "data": json.dumps(
                            {
                                "turn": result.turn,
                                "trace_id": result.trace_id,
                                "narrative": result.narrative,
                                "actions": result.actions,
                                "rejected": result.rejected,
                                "errors": result.errors,
                                "diff": result.diff,
                                "changes": ch,
                                "change_lines": format_change_lines(ch),
                                "state": result.state_snapshot.to_dict(),
                                "metrics": result.metrics,
                                "ruling": result.ruling,
                                "outcome_summary": result.outcome_summary,
                                "debug_mode": _app_mod.engine_config.debug_mode,
                                "outcome_hint": result.outcome_hint,
                                "scene_phase": result.scene_phase,
                                "summary": result.summary,
                                "ts": _ts_display,
                            }
                        ),
                    }
                    # Keep SSE open — frontend waits for world_done before closing
        except Exception as e:
            _app_mod.logger.exception("Turn failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@_app_mod.app.post("/turn/cancel")
async def cancel_turn():
    if err := _require_save():
        return err
    if not _app_mod._is_turn_in_progress():
        return JSONResponse({"ok": True})

    if _app_mod._cancel_event:
        _app_mod._cancel_event.set()
    released = await _app_mod._await_turn_done(timeout=30.0)
    if not released:
        _log.warning("cancel_turn timeout waiting for turn to finish")

    return JSONResponse({"ok": True, "cancelled": True})


@_app_mod.app.post("/turn/delete")
async def delete_last_turn():
    if err := _require_save():
        return err
    if _app_mod._is_turn_in_progress():
        return JSONResponse(
            {"error": "Turn already in progress"}, status_code=409
        )

    last_events = load_recent_turns(_app_mod.SAVE_DIR, 1)
    if not last_events:
        return JSONResponse(
            {"error": "No previous turn to delete"}, status_code=400
        )

    last_event = last_events[-1]
    actions = last_event.get("actions", [])
    pre_turn_state = last_event.get("last_turn_state")

    remove_last_event(_app_mod.SAVE_DIR)
    remove_last_chronicle_turn(_app_mod.SAVE_DIR)

    if pre_turn_state is not None:
        save_state(_app_mod.SAVE_DIR, pre_turn_state)
    else:
        _log.warning(
            "delete_last_turn last_turn_state missing for turn=%s — state not reverted",
            last_event.get("turn"),
        )

    _log.info("delete_last_turn turn=%s", last_event.get("turn"))
    return JSONResponse({"actions": actions, "turn": last_event.get("turn")})



@_app_mod.app.post("/new-game")
async def new_game(request: Request):
    form = await request.form()
    requested_pack = str(form.get("pack_id", "")).strip()
    if requested_pack and requested_pack != _app_mod._pack_id:
        try:
            _app_mod._active_pack = load_pack(requested_pack, _app_mod.PACKS_DIR)
            _app_mod._pack_id = requested_pack
            _app_mod.logger.info(
                "Switched pack to %s", _app_mod._pack_id
            )
        except Exception as exc:
            _app_mod.logger.error("Failed to switch pack %r: %s", requested_pack, exc)
            _log.error(
                "Unknown pack: %s", requested_pack,
                extra={"error_kind": ErrorKind.PACK_LOAD_FAILED},
            )
            return JSONResponse(
                status_code=400,
                content={"error": f"Failed to load pack '{requested_pack}': {exc}"},
            )

    pc_name = str(form.get("pc_name", "")).strip()
    pc_tagline = str(form.get("pc_tagline", "")).strip()
    pc_stats_raw = str(form.get("pc_stats", "")).strip()
    pc_hints = str(form.get("pc_hints", "")).strip()
    npc_hints = str(form.get("npc_hints", "")).strip()
    location_hints = str(form.get("location_hints", "")).strip()
    arc_hints = str(form.get("arc_hints", "")).strip()
    free_form = str(form.get("free_form", "")).strip()

    # Parse pc_stats JSON early — applied as a hard override after seed prep
    pc_stats_dict: dict[str, int] | None = None
    if pc_stats_raw:
        try:
            parsed = json.loads(pc_stats_raw)
            if isinstance(parsed, dict) and all(isinstance(v, int) for v in parsed.values()):
                pc_stats_dict = parsed
            else:
                _log.warning("new_game: invalid pc_stats shape: %s", pc_stats_raw)
        except json.JSONDecodeError:
            _log.warning("new_game: invalid pc_stats JSON: %s", pc_stats_raw)

    overrides = PlayerOverrides(
        pc_hints=pc_hints,
        npc_hints=npc_hints,
        location_hints=location_hints,
        arc_hints=arc_hints,
        free_form=free_form,
    )

    # Must capture BEFORE hint construction below — pc_stats/tagline/name get
    # folded into pc_hints, which would make is_empty() always return False and
    # skip dynamic seed generation for default char-creation submissions.
    has_hints = not overrides.is_empty()

    if (pc_name or pc_tagline) and overrides:
        hint_parts = []
        if pc_name:
            hint_parts.append(f"Name the PC '{pc_name}'.")
        if pc_tagline:
            hint_parts.append(f"Tagline: '{pc_tagline}'.")
        if hint_parts:
            overrides = overrides.model_copy(
                update={"pc_hints": " ".join(hint_parts) + " " + overrides.pc_hints}
            )

    try:
        # Dynamic seed path — always uses overrides (empty or not)
        _log.info("new_game dynamic seed pack=%s has_hints=%s", _app_mod._pack_id, has_hints)
        partial, pool_selection = await prepare_seed(
            _app_mod._active_pack,
            _app_mod.engine_config,
            template_dir=str(_app_mod.PROMPTS_DIR),
            overrides=overrides,
        )
        narrate_fields = await narrate_seed(
            partial.seed_state,
            _app_mod.engine_config,
            pack=_app_mod._active_pack,
            template_dir=str(_app_mod.PROMPTS_DIR),
            pool_selection=partial.pool_selection,
        )
        # Assemble final SeedEnvelope
        from ccya.pack import SeedEnvelope
        final_envelope = SeedEnvelope(
            seed_state=partial.seed_state,
            opening_narrative=narrate_fields["opening_narrative"],
            actions=narrate_fields["actions"],
            outcome_summary=narrate_fields["outcome_summary"],
            arc=partial.seed_state.arc,
            arc_origin=partial.seed_state.arc_origin,
        )
        seed = final_envelope.seed_state.model_dump(mode="json")
        seed["meta"]["setting_pack"] = _app_mod._pack_id
        if pc_stats_dict:
            seed.setdefault("pc", {})["stats"] = pc_stats_dict
        _apply_seed_to_save_dir(seed, final_envelope.opening_narrative, final_envelope.actions, outcome_summary=final_envelope.outcome_summary, pack_source=_app_mod._pack_id, pool_selection=pool_selection)
    except Exception as exc:
        _app_mod.logger.exception("new_game failed")
        return HTMLResponse(f"<p class='text-red-400'>Game creation failed: {exc}</p>", status_code=400)

    _log.info("new_game pack=%s", _app_mod._pack_id)
    ctx = _debug_context()
    ctx["state"] = _resolve_npc_ties(ctx["state"])
    return _app_mod._render("_state.html", ctx)


@_app_mod.app.post("/new-game/reroll")
async def new_game_reroll(request: Request):
    try:
        partial, pool_selection = await prepare_seed(
            _app_mod._active_pack,
            _app_mod.engine_config,
            template_dir=str(_app_mod.PROMPTS_DIR),
        )
        narrate_fields = await narrate_seed(
            partial.seed_state,
            _app_mod.engine_config,
            pack=_app_mod._active_pack,
            template_dir=str(_app_mod.PROMPTS_DIR),
            pool_selection=partial.pool_selection,
        )
        # Assemble final SeedEnvelope
        from ccya.pack import SeedEnvelope
        final_envelope = SeedEnvelope(
            seed_state=partial.seed_state,
            opening_narrative=narrate_fields["opening_narrative"],
            actions=narrate_fields["actions"],
            outcome_summary=narrate_fields["outcome_summary"],
            arc=partial.seed_state.arc,
            arc_origin=partial.seed_state.arc_origin,
        )
        seed = final_envelope.seed_state.model_dump(mode="json")
        seed["meta"]["setting_pack"] = _app_mod._pack_id
        _apply_seed_to_save_dir(seed, final_envelope.opening_narrative, final_envelope.actions, outcome_summary=final_envelope.outcome_summary, pack_source=_app_mod._pack_id, pool_selection=pool_selection)
    except Exception as exc:
        _app_mod.logger.exception("seed generation reroll failed")
        return HTMLResponse(f"<p class='text-red-400'>Re-roll failed: {exc}</p>")

    actions_html = "".join(
        f'<button class="action-pill" onclick="window._gameInstance && window._gameInstance.fillFromChoice(this.textContent)">{a}</button>'
        for a in narrate_fields["actions"]
    )
    return HTMLResponse(
        f'<div id="actions-zone" hx-swap-oob="outerHTML:true">{actions_html}</div>'
        + narrate_fields["opening_narrative"]
    )


@_app_mod.app.get("/panels/state")
def panel_state(request: Request):
    if err := _require_save():
        return err
    _log.debug("panel_state called")
    ctx = _debug_context()
    ctx["state"] = _resolve_npc_ties(ctx["state"])
    return _app_mod._render("_state.html", ctx)


def _resolve_npc_ties(state: WorldState) -> WorldState:
    """Resolve tie IDs to human-readable descriptions for the UI."""
    npcs = state.compendium.npcs
    # Build tie lookup: id → description from the active pack's scenario
    tie_lookup: dict[str, str] = {}
    try:
        scenario = _app_mod._active_pack.scenario
        if scenario and scenario.npc_bonds:
            tie_lookup = {b.id: b.description for b in scenario.npc_bonds if b.description}
    except Exception:
        pass

    updated: dict[str, NPCEntry] = {}
    for key, entry in npcs.items():
        updates: dict[str, Any] = {}
        # Ensure a display_name exists for sorting/templates when name is missing
        if not entry.name:
            updates["name"] = entry.title or key
        # Resolve tie ID to human-readable description
        raw_tie = entry.tie
        if raw_tie and raw_tie in tie_lookup:
            updates["tie_label"] = tie_lookup[raw_tie]
        if updates:
            updated[key] = entry.model_copy(update=updates)

    if not updated:
        return state
    merged = {**npcs, **updated}
    return state.model_copy(update={"compendium": state.compendium.model_copy(update={"npcs": merged})})


@_app_mod.app.get("/panels/state-left")
def panel_state_left(request: Request):
    if err := _require_save():
        return err
    state = _load_current_state()
    state = _resolve_npc_ties(state)
    return _app_mod._render("_state_left.html", {"state": state})


@_app_mod.app.get("/panels/state-right")
def panel_state_right(request: Request):
    if err := _require_save():
        return err
    _log.debug("panel_state_right called")
    return _app_mod._render("_state_right.html", _debug_context())


@_app_mod.app.get("/panels/actions")
def panel_actions(request: Request):
    if err := _require_save():
        return err
    return _app_mod._render("_actions.html", {"state": _load_current_state()})


@_app_mod.app.post("/panels/debug/clear-errors")
def debug_clear_errors():
    if err := _require_save():
        return err
    return _app_mod._render("_debug.html", _debug_context())


@_app_mod.app.get("/panels/debug")
def panel_debug():
    if err := _require_save():
        return err
    return _app_mod._render("_debug.html", _debug_context())


@_app_mod.app.delete("/packs/{pack_id:path}")
async def delete_pack(pack_id: str):
    # Only allow deleting custom/ or generated/ packs
    if not (pack_id.startswith("custom/") or pack_id.startswith("generated/")):
        return JSONResponse({"error": "Cannot delete built-in packs"}, status_code=403)
    try:
        pack_dir = _resolve_pack_dir(pack_id, _app_mod.PACKS_DIR)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=404)
    # Guard: don't delete if it's the currently active pack with an active game
    if _app_mod._pack_id == pack_id:
        return JSONResponse({"error": "Cannot delete the currently active pack"}, status_code=409)
    import shutil
    shutil.rmtree(pack_dir)
    _log.info("Deleted pack: %s", pack_id)
    return JSONResponse({"ok": True})


@_app_mod.app.get("/panels/pack-picker", response_class=HTMLResponse)
def panel_pack_picker():
    all_packs = list_packs(_app_mod.PACKS_DIR)
    custom_packs = [p for p in all_packs if p.id.startswith("custom/") or p.id.startswith("generated/")]
    default_packs = [p for p in all_packs if not p.id.startswith("custom/") and not p.id.startswith("generated/")]
    return _app_mod._render("_pack_picker.html", {
        "custom_packs": custom_packs,
        "default_packs": default_packs,
        "active_pack_id": _app_mod._pack_id,
    })


@_app_mod.app.get("/panels/char-creation", response_class=HTMLResponse)
def panel_char_creation():
    return _app_mod._render("_char_creation.html", {})


@_app_mod.app.get("/panels/world-builder", response_class=HTMLResponse)
def panel_world_builder():
    return _app_mod._render("_world_builder.html", {})


@_app_mod.app.post("/new-game/generate-pack")
async def new_game_generate_pack(request: Request):
    form = await request.form()
    concept = str(form.get("concept", "")).strip()
    world_name = str(form.get("world_name", "")).strip()
    tone_tags_raw = str(form.get("tone_tags", "[]")).strip()
    mood_note = str(form.get("mood_note", "")).strip()
    world_rules_raw = str(form.get("world_rules", "[]")).strip()

    trace_id = os.urandom(4).hex()

    _log.info(
        "new_game_generate_pack",
        extra={"trace_id": trace_id, "concept_len": len(concept)},
    )

    if not concept:
        async def _err():
            yield "data: {\"type\":\"generation_error\",\"error\":\"Concept is required.\"}\n\n"
        return StreamingResponse(_err(), media_type="text/event-stream")

    try:
        import json as _json
        tags = _json.loads(tone_tags_raw)
        rules = _json.loads(world_rules_raw)
    except Exception:
        tags = []
        rules = []

    inputs = {
        "concept": concept,
        "world_name": world_name,
        "tone_tags": tags,
        "mood_note": mood_note,
        "world_rules": rules,
    }

    packs_root = _app_mod.PACKS_DIR
    template_dir = str(_app_mod.PROMPTS_DIR)
    max_retries = _app_mod.engine_config.max_llm_retries

    from ccya.engine.generate_pack import generate_pack_from_brief

    async def _stream():
        async for event in generate_pack_from_brief(
            inputs=inputs,
            packs_root=packs_root,
            config=_app_mod.engine_config,
            template_dir=template_dir,
            trace_id=trace_id,
            max_retries=max_retries,
        ):
            yield f"data: {_json.dumps(event)}\n\n"

    return StreamingResponse(_stream(), media_type="text/event-stream")


@_app_mod.app.get("/panels/turn-log", response_class=HTMLResponse)
def panel_turn_log(limit: int = 50):
    if err := _require_save():
        return err
    lim = max(1, min(limit, 200))
    return _app_mod._render("_turn_log.html", {"entries": _turn_log_entries(_app_mod.SAVE_DIR, lim)})


@_app_mod.app.get("/turn_viewer", response_class=HTMLResponse)
def turn_viewer():
    css_path = _app_mod.BASE_DIR / "static" / "app.css"
    css_v = int(css_path.stat().st_mtime) if css_path.exists() else 0
    if _app_mod.SAVE_DIR is None:
        return _app_mod._render(
            "_turn_viewer.html",
            {"turns": [], "turn_count": 0, "no_events": True, "css_v": css_v, "no_save": True},
        )
    turns, no_events = _turn_viewer_data(_app_mod.SAVE_DIR)
    return _app_mod._render(
        "_turn_viewer.html",
        {
            "turns": turns,
            "turn_count": len(turns),
            "no_events": no_events,
            "css_v": css_v,
        },
    )


@_app_mod.app.get("/turn_viewer/data")
def turn_viewer_data():
    if err := _require_save():
        return err
    turns, no_events = _turn_viewer_data(_app_mod.SAVE_DIR)
    latest = turns[0] if turns else None
    return JSONResponse(
        {
            "turns": turns,
            "no_events": no_events,
            "turn_count": len(turns),
            "latest_turn": latest.get("turn") if latest else None,
            "latest_trace_id_full": latest.get("trace_id_full") if latest else None,
        }
    )


@_app_mod.app.get("/turn_viewer/stream")
async def turn_viewer_stream():
    path = _app_mod.SAVE_DIR / "events.jsonl"

    async def gen():
        last_mtime: float | None = None
        yield {"event": "open", "data": "{}"}
        while True:
            await asyncio.sleep(1.0)
            if not path.exists():
                continue
            m = path.stat().st_mtime
            if last_mtime is None:
                last_mtime = m
            elif m != last_mtime:
                last_mtime = m
                yield {"event": "updated", "data": "{}"}

    return EventSourceResponse(gen())


@_app_mod.app.get("/turn_viewer/prompts")
def turn_viewer_prompts(turn: int):
    """Load prompts for a specific turn from prompts.jsonl."""
    if err := _require_save():
        return err
    prompts_path = _app_mod.SAVE_DIR / "prompts.jsonl"
    if not prompts_path.exists():
        return JSONResponse({"prompts": []}, status_code=200)
    text = prompts_path.read_text().strip()
    if not text:
        return JSONResponse({"prompts": []}, status_code=200)
    all_prompts = []
    for line in text.splitlines():
        line = line.strip()
        if line:
            try:
                p = json.loads(line)
                if isinstance(p, dict) and p.get("turn") == turn:
                    all_prompts.append({
                        "stream": p.get("stream"),
                        "rendered_system": p.get("rendered_system", ""),
                        "rendered_user": p.get("rendered_user", ""),
                        "context_meta": p.get("context_meta"),
                    })
            except json.JSONDecodeError:
                continue
    return JSONResponse({"prompts": all_prompts}, status_code=200)


@_app_mod.app.get("/opening")
def opening():
    return HTMLResponse(_get_opening())


@_app_mod.app.get("/healthz")
def healthz():
    import httpx

    host = str(_app_mod.engine_config.host).rstrip("/")
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    if mock_mode:
        return {
            "llm": "mock",
            "model": _app_mod.engine_config.model,
            "available": True,
            "mock": True,
            "llm_version": "",
        }
    llm_version = ""
    try:
        with httpx.Client(timeout=5) as client:
            if "/api/chat" in host:
                resp = client.get(f"{host}/tags")
                resp.raise_for_status()
                body = resp.json()
                models = [m["name"] for m in body.get("models", [])]
            else:
                resp = client.get(f"{host}/models")
                resp.raise_for_status()
                body = resp.json()
                models = [m["id"] for m in body.get("data", [])]
            model = _app_mod.engine_config.model
            return {
                "llm": "ok",
                "model": model,
                "available": model in models,
                "llm_version": llm_version,
            }
    except Exception:
        return {
            "llm": "fail",
            "model": _app_mod.engine_config.model,
            "available": False,
            "llm_version": llm_version,
        }


@_app_mod.app.get("/api/settings")
async def get_settings():
    """Return the current 'game:' section of config.yaml."""
    game_config = _app_mod.config.get("game", {})
    # Flatten nested keys for UI consumption
    debug = game_config.get("debug", {}) or {}
    return JSONResponse({
        "thread_deescalate_on_success": game_config.get("thread_deescalate_on_success"),
        "warmup_on_start": game_config.get("warmup_on_start", False),
        "character_creation_enabled": game_config.get("character_creation_enabled", True),
        "debug_enabled": debug.get("enabled", False),
        "difficulty_curve": game_config.get("difficulty_curve", "balanced"),
        "scene_pressure_threshold": game_config.get("scene_pressure_threshold", 3),
        "scene_imperative_threshold": game_config.get("scene_imperative_threshold", 5),
        "near_miss_softening": game_config.get("near_miss_softening", True),
        "thread_memory_ttl": game_config.get("thread_memory_ttl", 3),
        "arc_memory_ttl": game_config.get("arc_memory_ttl", 3),
    })

@_app_mod.app.post("/api/settings")
async def post_settings(request: Request):
    """Update the 'game:' section of config.yaml and return updated values."""
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse({"error": "Expected JSON object"}, status_code=400)

    game_config = _app_mod.config.get("game", {})

    # Apply updates from request body

    for key in ("thread_deescalate_on_success", "warmup_on_start", "character_creation_enabled"):
        if key in data:
            val = bool(data[key])
            game_config[key] = val

    for key in ("scene_pressure_threshold", "scene_imperative_threshold", "thread_memory_ttl", "arc_memory_ttl"):
        if key in data:
            game_config[key] = int(data[key])

    if "difficulty_curve" in data:
        valid_curves = ("forgiving", "balanced", "demanding")
        curve_val = str(data["difficulty_curve"])
        if curve_val not in valid_curves:
            return JSONResponse({"error": f"Invalid difficulty_curve. Must be one of {valid_curves}"}, status_code=400)
        game_config["difficulty_curve"] = curve_val

    for key in ("near_miss_softening",):
        if key in data:
            game_config[key] = bool(data[key])

    debug_section = game_config.get("debug", {}) or {}
    if "debug_enabled" in data:
        debug_section["enabled"] = bool(data["debug_enabled"])
    game_config["debug"] = debug_section

    # Persist to disk
    from ccya.models import save_config as _save_config
    _save_config("config.yaml", _app_mod.config)

    # Update in-memory config reference so subsequent turns see new values
    _app_mod.config["game"] = game_config

    # Rebuild engine_config — game fields are read from cfg.get("game")
    from ccya.engine import build_engine_config as _build_engine_config
    _app_mod.engine_config = _build_engine_config(_app_mod.config)

    return await get_settings()  # Return updated state


@_app_mod.app.get("/api/saves")
async def list_saves():
    """List all available saves."""
    saves = _list_saves()
    return JSONResponse({"saves": saves})


def _is_valid_save_path(target: Path) -> bool:
    """Check target is under saves/ or evals/runs/ (path traversal guard)."""
    for root in [Path("saves"), Path("evals/runs")]:
        try:
            target.relative_to(root.resolve())
            return True
        except ValueError:
            _log.debug("_is_valid_save_path: %s not under %s", target, root.resolve())
            continue
    return False


@_app_mod.app.post("/api/switch-save")
async def switch_save(request: Request):
    """Switch to a different save directory."""
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse({"error": "Expected JSON object"}, status_code=400)

    save_name = str(data.get("save_name", "")).strip()
    if not save_name:
        return JSONResponse({"error": "Save name is required"}, status_code=400)

    # Try both root dirs to resolve the target
    target: Path | None = None
    for root in [Path("saves"), Path("evals/runs")]:
        candidate = (root / save_name).resolve()
        if _is_valid_save_path(candidate) and candidate.is_dir():
            target = candidate
            break
    if target is None:
        return JSONResponse({"error": "Invalid save path"}, status_code=400)

    _log.info("switch_save target=%s is_dir=%s", target, target.is_dir())
    if not target.is_dir():
        return JSONResponse({"error": f"Save directory not found: {save_name}"}, status_code=404)

    # Verify no turn is in progress on current save
    if _app_mod._is_turn_in_progress():
        return JSONResponse({"error": "Turn in progress, try again later"}, status_code=409)

    # Load state to verify it's valid
    try:
        state = load_state(target)
    except Exception as exc:
        _log.error("Failed to load state from %s: %s", save_name, exc)
        return JSONResponse({"error": f"Failed to load save: {exc}"}, status_code=500)

    # Clear turn state before switching
    _app_mod._turn_lock = _app_mod._cancel_event = _app_mod._turn_done_event = None

    # Switch
    _app_mod.SAVE_DIR = target
    _log.info("Switched save to %s", save_name)
    return JSONResponse({"ok": True, "save_dir": str(target), "state": state.model_dump()})


@_app_mod.app.post("/api/delete-save")
async def delete_save(request: Request):
    """Delete a save directory."""
    data = await request.json()
    if not isinstance(data, dict):
        return JSONResponse({"error": "Expected JSON object"}, status_code=400)

    save_name = str(data.get("save_name", "")).strip()
    if not save_name:
        return JSONResponse({"error": "Save name is required"}, status_code=400)

    # Prevent deleting the currently active save
    if save_name == _save_rel_name(_app_mod.SAVE_DIR):
        return JSONResponse({"error": "Cannot delete the currently active save"}, status_code=400)

    # Try both root dirs to resolve the target
    target: Path | None = None
    for root in [Path("saves"), Path("evals/runs")]:
        candidate = (root / save_name).resolve()
        if _is_valid_save_path(candidate):
            target = candidate
            break
    if target is None:
        return JSONResponse({"error": "Invalid save path"}, status_code=400)

    if not target.is_dir():
        return JSONResponse({"error": f"Save directory not found: {save_name}"}, status_code=404)

    # Verify no turn is in progress on current save
    if _app_mod._is_turn_in_progress():
        return JSONResponse({"error": "Turn in progress, try again later"}, status_code=409)

    try:
        import shutil
        shutil.rmtree(target)
    except OSError as exc:
        _log.error("Failed to delete save %s: %s", save_name, exc)
        return JSONResponse({"error": f"Failed to delete save: {exc}"}, status_code=500)

    _log.info("Deleted save %s", save_name)
    return JSONResponse({"ok": True})
