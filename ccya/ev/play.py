from __future__ import annotations

import asyncio
import logging
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from ccya.engine.config import EngineConfig, build_engine_config
from ccya.engine.turn import run_turn
from ccya.errors import LlmcError, LlmcTimeout
from ccya.models import TurnResult, load_config
from ccya.pack import load_pack
from ccya.state.io import _default_state, init_save_dir, load_state

_log = logging.getLogger(__name__)

EV_SAVES_DIR = Path("saves/ev")

_play_loop: asyncio.AbstractEventLoop | None = None


def _get_play_loop() -> asyncio.AbstractEventLoop:
    global _play_loop
    if _play_loop is None or _play_loop.is_closed():
        _play_loop = asyncio.new_event_loop()
    return _play_loop


def play_turn(
    input_text: str,
    state: dict[str, Any],
    config: EngineConfig,
    save_dir: Path,
    *,
    pack_name_locales: list[dict[str, Any]] | None = None,
    pack_narrator_rules: list[str] | None = None,
    pack_world_rules: list[str] | None = None,
    pack_factions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    loop = _get_play_loop()
    coro = _run_turn_async(
        input_text, state, config, save_dir,
        pack_name_locales=pack_name_locales,
        pack_narrator_rules=pack_narrator_rules,
        pack_world_rules=pack_world_rules,
        pack_factions=pack_factions,
    )
    return loop.run_until_complete(coro)


async def _run_turn_async(
    input_text: str,
    state: dict[str, Any],
    config: EngineConfig,
    save_dir: Path,
    *,
    pack_name_locales: list[dict[str, Any]] | None = None,
    pack_narrator_rules: list[str] | None = None,
    pack_world_rules: list[str] | None = None,
    pack_factions: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not (save_dir / "state.yaml").exists():
        init_save_dir(save_dir, state)

    narrative_chunks: list[str] = []
    turn_result: TurnResult | None = None
    t0 = time.monotonic()

    try:
        async for kind, payload in run_turn(
            save_dir=save_dir,
            user_input=input_text,
            config=config,
            pack_name_locales=pack_name_locales or [],
            pack_narrator_rules=pack_narrator_rules or [],
            pack_world_rules=pack_world_rules or [],
            pack_factions=pack_factions or [],
        ):
            if kind == "token":
                narrative_chunks.append(payload)
            elif kind == "complete":
                turn_result = payload
    except LlmcTimeout as exc:
        state_after = load_state(save_dir)
        return _build_error_output(
            state_after, [{"kind": "timeout", "message": str(exc)}], t0, narrative_chunks,
        )
    except LlmcError as exc:
        state_after = load_state(save_dir)
        return _build_error_output(
            state_after, [{"kind": "llmc_error", "message": str(exc)}], t0, narrative_chunks,
        )
    except Exception as exc:
        state_after = load_state(save_dir)
        return _build_error_output(
            state_after, [{"kind": "internal_error", "message": f"{type(exc).__name__}: {exc}"}], t0, narrative_chunks,
        )

    elapsed_ms = (time.monotonic() - t0) * 1000
    state_after = load_state(save_dir)

    if turn_result is None:
        return _build_error_output(
            state_after, [{"kind": "internal_error", "message": "Turn completed with no result"}], t0, narrative_chunks,
        )

    ruling = turn_result.ruling or {}
    momentum_before = ruling.get("momentum_before", 0.0)
    momentum_after = ruling.get("momentum_after", 0.0)

    scene = {
        "tags": state_after.get("scene", {}).get("tags", []),
        "tagline": state_after.get("scene", {}).get("tagline", ""),
        "id": state_after.get("location", {}).get("id", ""),
    }

    metrics = turn_result.metrics or {}
    ruling_metrics = metrics.get("ruling", {})
    narrate_metrics = metrics.get("narrate", {})
    extract_metrics = metrics.get("extract", {})
    tokens_in = ruling_metrics.get("tokens_in", 0) + narrate_metrics.get("tokens_in", 0) + extract_metrics.get("tokens_in", 0)
    tokens_out = ruling_metrics.get("tokens_out", 0) + narrate_metrics.get("tokens_out", 0) + extract_metrics.get("tokens_out", 0)

    return {
        "turn": turn_result.turn,
        "trace_id": turn_result.trace_id,
        "ruling": ruling,
        "narrative": turn_result.narrative,
        "momentum_before": momentum_before,
        "momentum_after": momentum_after,
        "momentum_delta": momentum_after - momentum_before,
        "actions": turn_result.actions,
        "scene": scene,
        "applied": turn_result.applied,
        "errors": turn_result.errors or [],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "ms": round(elapsed_ms, 1),
    }


def _build_error_output(state: dict[str, Any], errors: list[dict[str, Any]], t0: float, narrative_chunks: list[str]) -> dict[str, Any]:
    elapsed_ms = (time.monotonic() - t0) * 1000
    narrative = "".join(narrative_chunks) if narrative_chunks else "*An error occurred...*"
    return {
        "turn": state.get("meta", {}).get("turn", 0),
        "trace_id": "",
        "ruling": {},
        "narrative": narrative,
        "momentum_before": state.get("pc", {}).get("momentum", 0.0),
        "momentum_after": state.get("pc", {}).get("momentum", 0.0),
        "momentum_delta": 0.0,
        "actions": [],
        "scene": {
            "tags": state.get("scene", {}).get("tags", []),
            "tagline": state.get("scene", {}).get("tagline", ""),
            "id": state.get("location", {}).get("id", ""),
        },
        "applied": {},
        "errors": errors,
        "tokens_in": 0,
        "tokens_out": 0,
        "ms": round(elapsed_ms, 1),
    }


def format_play_output(result: dict[str, Any]) -> str:
    lines = []
    lines.append(f"Turn {result['turn']}  |  trace: {result['trace_id']}")
    lines.append("-" * 54)

    ruling = result.get("ruling", {})
    if ruling.get("intent_verb"):
        skill = ruling.get("skill", "?")
        diff = ruling.get("difficulty", "?")
        band = ruling.get("band", "?")
        momentum_delta_ruling = ruling.get("momentum_delta", 0)
        lines.append(f"Ruling:    {ruling.get('intent_verb', '?').upper()} (skill: {skill}, diff: {diff})")
        if ruling.get("rolled"):
            dice = ruling.get("dice", "?")
            lines.append(f"           Roll: {dice} -> Band: {band} ({momentum_delta_ruling:+d} momentum)")

    narrative = result.get("narrative", "")
    lines.append(f"Narrative: \"{narrative[:60]}{'...' if len(narrative) > 60 else ''}\" ({len(narrative)} chars)")
    lines.append("")

    mb = result.get("momentum_before", 0)
    ma = result.get("momentum_after", 0)
    md = result.get("momentum_delta", 0)
    lines.append(f"Momentum:   {mb} -> {ma}  ({md:+d})")

    actions = result.get("actions", [])
    lines.append(f"Actions:   {', '.join(actions) if actions else 'none'}")

    scene = result.get("scene", {})
    scene_tags = scene.get("tags", [])
    scene_tagline = scene.get("tagline", "")
    scene_id = scene.get("id", "")
    scene_parts = [s for s in [scene_id, scene_tagline] if s] + scene_tags
    lines.append(f"Scene:     {', '.join(scene_parts) if scene_parts else 'unknown'}")

    applied = result.get("applied", {})
    if applied:
        lines.append("")
        lines.append("Deltas:")
        for k, v in applied.items():
            if isinstance(v, list) and v:
                for item in v:
                    if isinstance(item, dict):
                        item_id = item.get("id", item.get("name", ""))
                        item_name = item.get("name", "")
                        label = f"{item_id}: {item_name}" if item_name else item_id
                        lines.append(f"  {k}: {label}")
                    else:
                        lines.append(f"  {k}: {item}")
            elif isinstance(v, dict) and v:
                for sk, sv in v.items():
                    lines.append(f"  {k}: {sk} -> {sv}")
            elif v:
                lines.append(f"  {k}: {v}")

    errors = result.get("errors", [])
    lines.append("")
    if errors:
        lines.append("Errors:")
        for err in errors:
            lines.append(f"  - {err.get('kind', 'unknown')}: {err.get('message', '')}")
    else:
        lines.append("Errors:    none")

    ti = result.get("tokens_in", 0)
    to = result.get("tokens_out", 0)
    ms = result.get("ms", 0)
    lines.append(f"Tokens:    in={ti}  out={to}  ms={ms}")

    return "\n".join(lines)


def format_error_output(result: dict[str, Any]) -> str:
    lines = []
    lines.append(f"Turn {result['turn']}  |  trace: {result['trace_id']}")
    lines.append("-" * 54)
    lines.append("Errors:")
    for err in result.get("errors", []):
        lines.append(f"  - {err.get('kind', 'unknown')}: {err.get('message', '')}")
    narrative = result.get("narrative", "")
    lines.append(f"  - Fallback narrative: \"{narrative[:60]}{'...' if len(narrative) > 60 else ''}\"")
    lines.append("")
    ti = result.get("tokens_in", 0)
    to = result.get("tokens_out", 0)
    ms = result.get("ms", 0)
    lines.append(f"Tokens:    in={ti}  out={to}  ms={ms}")
    return "\n".join(lines)


def _create_play_session(pack: str | None = None, packs_dir: Path | None = None) -> Path:
    now = datetime.now()
    rand_suffix = uuid.uuid4().hex[:6]
    session_name = now.strftime("%Y%m%d_%H%M%S_") + rand_suffix
    session_dir = EV_SAVES_DIR / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    if pack:
        packs_dir = packs_dir or Path("packs")
        p = load_pack(pack, packs_dir)
        if p.seed:
            state_dict = p.seed.model_dump()
        else:
            state_dict = _default_state()
    else:
        state_dict = _default_state()

    init_save_dir(session_dir, state_dict)

    latest_link = EV_SAVES_DIR / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    latest_link.symlink_to(session_dir)

    return session_dir


def _build_play_config(flags: dict[str, str]) -> EngineConfig:
    raw_cfg = load_config()
    if "model" in flags:
        raw_cfg.setdefault("llm", {})["model"] = flags["model"]
    if "temp" in flags:
        temp = float(flags["temp"])
        for section in ("ruling", "extract", "narrate", "generate_seed"):
            raw_cfg.setdefault("llm", {}).setdefault(section, {})["temperature"] = temp

    config = build_engine_config(raw_cfg)

    if "no-sanitize" in flags:
        config.sanitize_every = 0

    return config


def _load_pack_params(pack_id: str | None, packs_dir: Path | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str], list[str], list[dict[str, str]]]:
    if not pack_id:
        return None, [], [], [], []

    packs_dir = packs_dir or Path("packs")
    p = load_pack(pack_id, packs_dir)
    scenario = p.scenario
    return (
        p.seed.model_dump() if p.seed else None,
        scenario.name_locales if scenario else p.manifest.name_locales,
        scenario.narrator_rules if scenario else [],
        scenario.world_rules if scenario else [],
        [f.model_dump() for f in (scenario.factions if scenario else [])],
    )


def _interactive_session(config: EngineConfig, pack: str | None = None) -> None:
    seed_dict, name_locales, narrator_rules, world_rules, factions = _load_pack_params(pack)
    session_dir = _create_play_session(pack=pack)
    state = load_state(session_dir)
    turns_played = 0
    trace_ids: list[str] = []

    print(f"Interactive session started. Session: {session_dir}")
    print("Type 'quit' or 'exit' to end, Ctrl+D to exit.")
    print()

    while True:
        try:
            user_input = input("> ")
        except EOFError:
            break

        if user_input.strip().lower() in ("quit", "exit"):
            break

        if not user_input.strip():
            continue

        result = play_turn(
            user_input, state, config, session_dir,
            pack_name_locales=name_locales,
            pack_narrator_rules=narrator_rules,
            pack_world_rules=world_rules,
            pack_factions=factions,
        )
        turns_played += 1
        trace_ids.append(result.get("trace_id", ""))

        if result.get("errors"):
            print(format_error_output(result))
        else:
            print(format_play_output(result))

        state = load_state(session_dir)

    print()
    print(f"Session ended. Turns: {turns_played}")
    print(f"Traces: {', '.join(trace_ids)}")
    print(f"Events: {session_dir / 'events.jsonl'}")


def _llm_session(config: EngineConfig, max_turns: int = 20, pack: str | None = None) -> None:
    seed_dict, name_locales, narrator_rules, world_rules, factions = _load_pack_params(pack)
    session_dir = _create_play_session(pack=pack)
    state = load_state(session_dir)
    turns_played = 0
    trace_ids: list[str] = []

    system_prompt = (
        "You are roleplaying as a player in a text adventure game. "
        "Given the current scene, your recent actions, and the available options, "
        "decide what to do next. Respond with a short, natural language action. "
        "Do not narrate. Do not use meta-language. Just say what your character does."
    )

    recent_summaries: list[str] = []

    for turn_i in range(max_turns):
        scene = state.get("scene", {})
        scene_tags = scene.get("tags", [])
        scene_tagline = scene.get("tagline", "")
        location = state.get("location", {})
        location_name = location.get("name", "")

        context_parts = [f"Location: {location_name or 'unknown'}"]
        if scene_tagline:
            context_parts.append(f"Scene: {scene_tagline}")
        if scene_tags:
            context_parts.append(f"Tags: {', '.join(scene_tags)}")
        if recent_summaries:
            context_parts.append("Recent events:")
            context_parts.extend(f"  {s}" for s in recent_summaries[-3:])

        user_prompt = "\n".join(context_parts) + "\n\nWhat do you do?"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        from ccya.llm_client import chat as llm_chat

        try:
            loop = _get_play_loop()
            response = loop.run_until_complete(
                llm_chat(
                    config.host,
                    config.model,
                    messages,
                    temperature=config.narrate_temperature,
                    timeout=float(config.request_timeout_s),
                ),
            )
            player_input = response.get("response", "").strip()
        except Exception as exc:
            print(f"LLM player error: {exc}")
            break

        if not player_input:
            break

        print(f"\n[Player] {player_input}")

        result = play_turn(
            player_input, state, config, session_dir,
            pack_name_locales=name_locales,
            pack_narrator_rules=narrator_rules,
            pack_world_rules=world_rules,
            pack_factions=factions,
        )
        turns_played += 1
        trace_ids.append(result.get("trace_id", ""))

        if result.get("errors"):
            print(format_error_output(result))
        else:
            print(format_play_output(result))

        narrative = result.get("narrative", "")
        if narrative:
            recent_summaries.append(narrative[:200])

        state = load_state(session_dir)

    print()
    print(f"Session ended. Turns: {turns_played}")
    print(f"Traces: {', '.join(trace_ids)}")
    print(f"Events: {session_dir / 'events.jsonl'}")


def cmd_play(flags: dict[str, str], args: list[str]) -> None:
    if "interactive" in flags:
        config = _build_play_config(flags)
        _interactive_session(config, pack=flags.get("pack"))
        sys.exit(0)

    if "llm" in flags:
        config = _build_play_config(flags)
        max_turns = int(flags.get("turns", "20"))
        _llm_session(config, max_turns=max_turns, pack=flags.get("pack"))
        sys.exit(0)

    if len(args) < 2:
        print("Usage: ev.py play <input> [--save-dir DIR] [--no-sanitize] [--model MODEL] [--temp TEMP] [--pack PACK]", file=sys.stderr)
        sys.exit(1)

    input_text = args[1]

    pack_id = flags.get("pack")
    seed_dict, name_locales, narrator_rules, world_rules, factions = _load_pack_params(pack_id)

    if "save-dir" in flags:
        save_dir = Path(flags["save-dir"])
        state = load_state(save_dir)
    elif pack_id:
        session_dir = _create_play_session(pack=pack_id)
        save_dir = session_dir
        state = load_state(save_dir)
    else:
        session_dir = _create_play_session()
        save_dir = session_dir
        state = load_state(save_dir)

    config = _build_play_config(flags)

    result = play_turn(
        input_text, state, config, save_dir,
        pack_name_locales=name_locales,
        pack_narrator_rules=narrator_rules,
        pack_world_rules=world_rules,
        pack_factions=factions,
    )

    if result.get("errors"):
        print(format_error_output(result))
    else:
        print(format_play_output(result))

    if result.get("errors"):
        sys.exit(1)
    sys.exit(0)
