"""All HTMX route handlers (@app.get / @app.post)."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from ccya.engine import (
    format_change_lines,
    generate_seed,
    is_turn_in_progress,
    run_turn,
    run_turn_retry,
)
from ccya.engine.names import generate_faction_pool, generate_location_pool
from ccya.models import IntentEnvelope, RulesOutcome
from ccya.pack import PlayerOverrides, load_pack, list_packs
from ccya.state import (
    init_save_dir,
    load_recent_events,
    remove_last_chronicle_turn,
    remove_last_event,
)
from .panels import (
    _debug_context,
    _get_opening,
    _get_opening_actions,
    _load_current_state,
    _load_last_actions,
    _load_recent_history,
)
from .metrics import _turn_log_entries
from .tv import _turn_viewer_data

# Import the app module to reference its globals (enables test patching)
_app_mod = sys.modules["ccya.server.app"]


def _format_ts(ts_str: str) -> str:
    """Convert UTC ISO string to a human-readable display string."""
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b · %I:%M %p UTC").lstrip("0")
    except (ValueError, AttributeError):
        return ts_str  # fallback: return raw if unparseable


@_app_mod.app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    history = _load_recent_history(_app_mod.SAVE_DIR)
    last_actions = _load_last_actions(_app_mod.SAVE_DIR) if history else []
    state = _load_current_state()
    opening = (
        _get_opening() if not history and state.get("location", {}).get("id") else ""
    )
    opening_actions = _get_opening_actions() if not history and opening else []
    ctx = _debug_context()
    ctx["state"] = state
    ctx["history"] = history
    ctx["last_actions"] = last_actions
    ctx["opening"] = opening
    ctx["opening_actions"] = opening_actions
    ctx["has_narrative"] = bool(opening or history)
    ctx["pack_mode"] = _app_mod._active_pack.mode
    ctx["pack_name"] = _app_mod._active_pack.manifest.name
    ctx["character_creation_enabled"] = _app_mod.config.get("game", {}).get(
        "character_creation_enabled", True
    )
    css_path = _app_mod.BASE_DIR / "static" / "app.css"
    ctx["css_v"] = int(css_path.stat().st_mtime) if css_path.exists() else 0
    return _app_mod._render("index.html", ctx)


@_app_mod.app.get("/turn")
async def get_turn(input: str = ""):
    user_input = input.strip()
    if not user_input:

        async def _empty():
            yield {"event": "turn_error", "data": json.dumps({"error": "Empty input"})}

        return EventSourceResponse(_empty())

    if is_turn_in_progress(str(_app_mod.SAVE_DIR)):

        async def _busy():
            yield {
                "event": "turn_error",
                "data": json.dumps({"error": "Turn already in progress"}),
            }

        return EventSourceResponse(_busy())

    async def event_stream():
        try:
            async for kind, payload in run_turn(
                _app_mod.SAVE_DIR,
                user_input,
                config=_app_mod.engine_config,
                template_dir=str(_app_mod.PROMPTS_DIR),
                pack_style=_app_mod._active_pack.style_text,
                pack_name_locales=_app_mod._active_pack.manifest.name_locales,
                pack_factions=[f.model_dump() for f in (_app_mod._active_pack.scenario.factions if _app_mod._active_pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (_app_mod._active_pack.scenario.locations if _app_mod._active_pack.scenario else [])],
                pack_narrator_rules=_app_mod._active_pack.scenario.narrator_rules if _app_mod._active_pack.scenario else [],
                pack_world_rules=_app_mod._active_pack.scenario.world_rules if _app_mod._active_pack.scenario else [],
            ):
                if kind == "token":
                    yield {
                        "event": "narrative_token",
                        "data": json.dumps({"chunk": payload}),
                    }
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        _app_mod._ERRORS_LOG.appendleft(err)
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
                                "scene_tags": result.scene_tags,
                                "game_over": "game_over" in (result.scene_tags or []),
                                "rejected": result.rejected,
                                "errors": result.errors,
                                "diff": result.diff,
                                "changes": ch,
                                "change_lines": format_change_lines(ch),
                                "state": _load_current_state(),
                                "metrics": result.metrics,
                                "rules": result.rules,
                                "recent_events_evicted": result.recent_events_evicted,
                                "ts": _ts_display,
                            }
                        ),
                    }
        except Exception as e:
            _app_mod.logger.exception("Turn failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@_app_mod.app.get("/turn/retry")
async def retry_turn():
    if is_turn_in_progress(str(_app_mod.SAVE_DIR)):
        return JSONResponse(
            {"error": "Turn already in progress"}, status_code=409
        )

    last_events = load_recent_events(_app_mod.SAVE_DIR, 1)
    if not last_events:
        return JSONResponse(
            {"error": "No previous turn to retry"}, status_code=400
        )

    last_event = last_events[-1]
    rules_data = last_event.get("rules", {}) or {}

    rules_outcome = RulesOutcome(
        rolled=rules_data.get("rolled", False),
        skill=rules_data.get("skill", ""),
        stat_value=0,
        difficulty=rules_data.get("difficulty", "normal"),
        stat_mod=rules_data.get("stat_mod", 0),
        diff_mod=rules_data.get("diff_mod", 0),
        cond_mod=rules_data.get("cond_mod", 0),
        dice=rules_data.get("dice", []),
        raw_total=rules_data.get("raw_total", 0),
        final_total=rules_data.get("final_total", 0),
        band=rules_data.get("band", "success"),
        directive=rules_data.get("directive", ""),
        intent_verb=rules_data.get("intent_verb", "act"),
        intent=rules_data.get("intent", ""),
    )

    intent = IntentEnvelope(
        intent=rules_outcome.intent,
        intent_verb=rules_outcome.intent_verb,
    )

    remove_last_event(_app_mod.SAVE_DIR)
    remove_last_chronicle_turn(_app_mod.SAVE_DIR)

    async def event_stream():
        try:
            async for kind, payload in run_turn_retry(
                _app_mod.SAVE_DIR,
                rules_outcome,
                intent,
                config=_app_mod.engine_config,
                template_dir=str(_app_mod.PROMPTS_DIR),
                pack_style=_app_mod._active_pack.style_text,
                pack_name_locales=_app_mod._active_pack.manifest.name_locales,
                pack_factions=[f.model_dump() for f in (_app_mod._active_pack.scenario.factions if _app_mod._active_pack.scenario else [])],
                pack_locations=[loc.model_dump() for loc in (_app_mod._active_pack.scenario.locations if _app_mod._active_pack.scenario else [])],
                pack_narrator_rules=_app_mod._active_pack.scenario.narrator_rules if _app_mod._active_pack.scenario else [],
                pack_world_rules=_app_mod._active_pack.scenario.world_rules if _app_mod._active_pack.scenario else [],
            ):
                if kind == "token":
                    yield {
                        "event": "narrative_token",
                        "data": json.dumps({"chunk": payload}),
                    }
                elif kind == "phase":
                    yield {"event": "phase", "data": json.dumps(payload)}
                elif kind == "complete":
                    result = payload
                    for err in result.errors:
                        _app_mod._ERRORS_LOG.appendleft(err)
                    ch = result.changes if isinstance(result.changes, dict) else {}
                    _ts_display = _format_ts(result.ts)
                    yield {
                        "event": "turn_complete",
                        "data": json.dumps(
                            {
                                "turn": result.turn,
                                "trace_id": result.trace_id,
                                "narrative": result.narrative,
                                "actions": result.actions,
                                "scene_tags": result.scene_tags,
                                "game_over": "game_over" in (result.scene_tags or []),
                                "rejected": result.rejected,
                                "errors": result.errors,
                                "diff": result.diff,
                                "changes": ch,
                                "change_lines": format_change_lines(ch),
                                "state": _load_current_state(),
                                "metrics": result.metrics,
                                "rules": result.rules,
                                "retry": True,
                                "recent_events_evicted": result.recent_events_evicted,
                                "ts": _ts_display,
                            }
                        ),
                    }
        except Exception as e:
            _app_mod.logger.exception("Retry failed")
            yield {"event": "turn_error", "data": json.dumps({"error": str(e)})}

    return EventSourceResponse(event_stream())


@_app_mod.app.post("/new-game")
async def new_game(request: Request):
    _app_mod._ERRORS_LOG.clear()

    form = await request.form()
    requested_pack = str(form.get("pack_id", "")).strip()
    if requested_pack and requested_pack != _app_mod._pack_id:
        try:
            _app_mod._active_pack = load_pack(requested_pack, _app_mod.PACKS_DIR)
            _app_mod._pack_id = requested_pack
            _app_mod.logger.info(
                "Switched pack to %s (mode=%s)", _app_mod._pack_id, _app_mod._active_pack.mode
            )
        except Exception as exc:
            _app_mod.logger.error("Failed to switch pack %r: %s", requested_pack, exc)
            _app_mod._ERRORS_LOG.appendleft({"message": f"Unknown pack: {requested_pack}"})

    pc_name = str(form.get("pc_name", "")).strip()
    pc_tagline = str(form.get("pc_tagline", "")).strip()
    pc_stats_raw = str(form.get("pc_stats", "")).strip()
    pc_hints = str(form.get("pc_hints", "")).strip()
    npc_hints = str(form.get("npc_hints", "")).strip()
    location_hints = str(form.get("location_hints", "")).strip()
    quest_hints = str(form.get("quest_hints", "")).strip()
    free_form = str(form.get("free_form", "")).strip()

    npc_count_raw = str(form.get("npc_count", "")).strip()
    try:
        npc_count = max(0, int(npc_count_raw)) if npc_count_raw else 0
    except ValueError:
        npc_count = 0

    overrides = PlayerOverrides(
        pc_hints=pc_hints,
        npc_hints=npc_hints,
        location_hints=location_hints,
        quest_hints=quest_hints,
        free_form=free_form,
        npc_count=npc_count,
    )

    if (pc_name or pc_tagline or pc_stats_raw) and overrides:
        hint_parts = []
        if pc_name:
            hint_parts.append(f"Name the PC '{pc_name}'.")
        if pc_tagline:
            hint_parts.append(f"Tagline: '{pc_tagline}'.")
        if pc_stats_raw:
            hint_parts.append(f"Use these exact stats: {pc_stats_raw}.")
        if hint_parts:
            overrides = overrides.model_copy(
                update={"pc_hints": " ".join(hint_parts) + " " + overrides.pc_hints}
            )

    if _app_mod._active_pack.mode == "static":
        assert _app_mod._active_pack.seed is not None
        seed = _app_mod._active_pack.seed.model_dump()
        if pc_name:
            seed["pc"]["name"] = pc_name
        if pc_tagline:
            seed["pc"]["tagline"] = pc_tagline
        if pc_stats_raw:
            try:
                stats = json.loads(pc_stats_raw)
                if _app_mod._validate_stats(stats):
                    seed["pc"]["stats"] = stats
            except (json.JSONDecodeError, TypeError):
                pass
        seed.setdefault("meta", {})["model"] = _app_mod.config["llm"]["model"]
        init_save_dir(_app_mod.SAVE_DIR, seed)
        _app_mod._dynamic_opening = ""
        _app_mod._dynamic_opening_actions = []
    else:
        try:
            envelope = await generate_seed(
                _app_mod._active_pack,
                _app_mod.engine_config,
                template_dir=str(_app_mod.PROMPTS_DIR),
                overrides=overrides if not overrides.is_empty() else None,
            )
            seed = envelope.seed_state.model_dump()
            seed.setdefault("meta", {})["model"] = _app_mod.config["llm"]["model"]
            seed["meta"]["setting_pack"] = _app_mod._pack_id
            # Phase 5: seed world factions and locations
            meta = seed.setdefault("meta", {})
            faction_seed = meta.pop("faction_pool_seed", None)
            location_seed = meta.pop("location_pool_seed", None)
            seed.setdefault("world", {})["factions"] = generate_faction_pool(faction_seed)
            seed.setdefault("world", {})["locations"] = generate_location_pool(location_seed)
            init_save_dir(_app_mod.SAVE_DIR, seed)
            _app_mod._dynamic_opening = envelope.opening_narrative
            _app_mod._dynamic_opening_actions = envelope.actions
        except Exception as exc:
            _app_mod.logger.exception("generate_seed failed")
            _app_mod._ERRORS_LOG.appendleft({"message": f"New game generation failed: {exc}"})

    ctx = _debug_context()
    ctx["pack_mode"] = _app_mod._active_pack.mode
    return _app_mod._render("_state.html", ctx)


@_app_mod.app.post("/new-game/reroll")
async def new_game_reroll(request: Request):
    if _app_mod._active_pack.mode != "dynamic":
        return HTMLResponse(
            "<p>Re-roll only available for dynamic packs.</p>", status_code=400
        )

    try:
        envelope = await generate_seed(
            _app_mod._active_pack,
            _app_mod.engine_config,
            template_dir=str(_app_mod.PROMPTS_DIR),
        )
        seed = envelope.seed_state.model_dump()
        seed.setdefault("meta", {})["model"] = _app_mod.config["llm"]["model"]
        seed["meta"]["setting_pack"] = _app_mod._pack_id
        # Phase 5: seed world factions and locations
        meta = seed.setdefault("meta", {})
        faction_seed = meta.pop("faction_pool_seed", None)
        location_seed = meta.pop("location_pool_seed", None)
        seed.setdefault("world", {})["factions"] = generate_faction_pool(faction_seed)
        seed.setdefault("world", {})["locations"] = generate_location_pool(location_seed)
        init_save_dir(_app_mod.SAVE_DIR, seed)
        _app_mod._dynamic_opening = envelope.opening_narrative
        _app_mod._dynamic_opening_actions = envelope.actions
    except Exception as exc:
        _app_mod.logger.exception("generate_seed reroll failed")
        _app_mod._ERRORS_LOG.appendleft({"message": f"Re-roll failed: {exc}"})
        return HTMLResponse(f"<p class='text-red-400'>Re-roll failed: {exc}</p>")

    actions_html = "".join(
        f'<button class="action-pill" onclick="window._gameInstance && window._gameInstance.fillFromChoice(this.textContent)">{a}</button>'
        for a in _app_mod._dynamic_opening_actions
    )
    return HTMLResponse(
        f'<div id="actions-zone" hx-swap-oob="outerHTML:true">{actions_html}</div>'
        + _app_mod._dynamic_opening
    )


@_app_mod.app.get("/panels/state")
def panel_state(request: Request):
    return _app_mod._render("_state.html", _debug_context())


@_app_mod.app.get("/panels/state-left")
def panel_state_left(request: Request):
    return _app_mod._render("_state_left.html", {"state": _load_current_state()})


@_app_mod.app.get("/panels/state-right")
def panel_state_right(request: Request):
    return _app_mod._render("_state_right.html", _debug_context())


@_app_mod.app.get("/panels/actions")
def panel_actions(request: Request):
    return _app_mod._render("_actions.html", {"state": _load_current_state()})


@_app_mod.app.post("/panels/debug/clear-errors")
def debug_clear_errors():
    _app_mod._ERRORS_LOG.clear()
    return _app_mod._render("_debug.html", _debug_context())


@_app_mod.app.get("/panels/debug")
def panel_debug():
    return _app_mod._render("_debug.html", _debug_context())


@_app_mod.app.get("/panels/pack-picker", response_class=HTMLResponse)
def panel_pack_picker():
    packs = list_packs(_app_mod.PACKS_DIR)
    return _app_mod._render("_pack_picker.html", {"packs": packs, "active_pack_id": _app_mod._pack_id})


@_app_mod.app.get("/panels/char-creation", response_class=HTMLResponse)
def panel_char_creation():
    return _app_mod._render("_char_creation.html", {})


@_app_mod.app.get("/panels/turn-log", response_class=HTMLResponse)
def panel_turn_log(limit: int = 50):
    lim = max(1, min(limit, 200))
    return _app_mod._render("_turn_log.html", {"entries": _turn_log_entries(_app_mod.SAVE_DIR, lim)})


@_app_mod.app.get("/turn_viewer", response_class=HTMLResponse)
def turn_viewer():
    css_path = _app_mod.BASE_DIR / "static" / "app.css"
    css_v = int(css_path.stat().st_mtime) if css_path.exists() else 0
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


@_app_mod.app.get("/opening")
def opening():
    return HTMLResponse(_get_opening())


@_app_mod.app.get("/healthz")
def healthz():
    import httpx

    host = str(_app_mod.config["llm"]["host"]).rstrip("/")
    mock_mode = os.environ.get("MOCK_MODE", "").lower() in ("true", "1", "yes")
    if mock_mode:
        return {
            "llm": "mock",
            "model": _app_mod.config["llm"]["model"],
            "available": True,
            "mock": True,
            "llm_version": "",
        }
    llm_version = ""
    try:
        with httpx.Client(timeout=5) as client:
            resp = client.get(f"{host}/models")
            resp.raise_for_status()
            body = resp.json()
            models = [m["id"] for m in body.get("data", [])]
            model = _app_mod.config["llm"]["model"]
            return {
                "llm": "ok",
                "model": model,
                "available": model in models,
                "llm_version": llm_version,
            }
    except Exception:
        return {
            "llm": "fail",
            "model": _app_mod.config["llm"]["model"],
            "available": False,
            "llm_version": llm_version,
        }
