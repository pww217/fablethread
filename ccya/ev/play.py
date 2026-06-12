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
from ccya.engine.seed import generate_seed
from ccya.engine.turn import run_turn
from ccya.errors import LlmcError, LlmcTimeout
from ccya.models import TurnResult, load_config
from ccya.pack import load_pack, list_packs
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
    lines.append(f"Momentum:   {mb} -> {ma}  ({md:+.1f})")

    actions = result.get("actions", [])
    lines.append(f"Actions:   {', '.join(actions) if actions else 'none'}")

    scene = result.get("scene", {})
    scene_tagline = scene.get("tagline", "")
    scene_id = scene.get("id", "")
    scene_parts = [s for s in [scene_id, scene_tagline] if s]
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


def _ensure_seed_generated(
    save_dir: Path,
    pack_id: str | None,
    config: EngineConfig,
    *,
    packs_dir: Path | None = None,
) -> dict[str, Any]:
    if pack_id is None:
        return load_state(save_dir)

    packs_dir = packs_dir or Path("packs")
    p = load_pack(pack_id, packs_dir)
    if p.scenario is not None:
        loop = _get_play_loop()
        envelope, pool_selection = loop.run_until_complete(
            generate_seed(p, config, template_dir=str(Path(__file__).parent.parent / "prompts")),
        )
        seed_dict = envelope.seed_state.model_dump(mode="json")
        seed_dict.setdefault("meta", {})["setting_pack"] = pack_id
        seed_dict.setdefault("meta", {})["_seed_type"] = "dynamic"
        seed_dict.setdefault("meta", {})["_pack_source"] = pack_id
        if envelope.opening_narrative:
            seed_dict["__seed_meta__"] = {
                "opening_narrative": envelope.opening_narrative,
                "actions": envelope.actions or [],
                "outcome_summary": envelope.outcome_summary or "",
            }
        if pool_selection:
            seed_dict["__seed_pools__"] = pool_selection
        init_save_dir(save_dir, seed_dict)

    return load_state(save_dir)


def _create_play_session(pack: str | None = None, packs_dir: Path | None = None) -> Path:
    now = datetime.now()
    rand_suffix = uuid.uuid4().hex[:6]
    session_name = now.strftime("%Y%m%d_%H%M%S_") + rand_suffix
    session_dir = EV_SAVES_DIR / session_name
    session_dir.mkdir(parents=True, exist_ok=True)

    if pack:
        packs_dir = packs_dir or Path("packs")
        p = load_pack(pack, packs_dir)
        if p.scenario is None:
            if p.seed:
                state_dict = p.seed.model_dump()
            else:
                state_dict = _default_state()
            if p.opening_scene and not state_dict.get("__seed_meta__", {}).get("opening_narrative"):
                state_dict.setdefault("__seed_meta__", {})["opening_narrative"] = p.opening_scene
            init_save_dir(session_dir, state_dict)
    else:
        init_save_dir(session_dir, _default_state())

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


def _load_pack_params(pack_id: str | None, packs_dir: Path | None = None) -> tuple[dict[str, Any] | None, list[dict[str, Any]], list[str], list[str], list[dict[str, str]], str | None, str | None]:
    if not pack_id:
        return None, [], [], [], [], None, None

    packs_dir = packs_dir or Path("packs")
    p = load_pack(pack_id, packs_dir)
    scenario = p.scenario
    return (
        p.seed.model_dump() if p.seed else None,
        scenario.name_locales if scenario else p.manifest.name_locales,
        scenario.narrator_rules if scenario else [],
        scenario.world_rules if scenario else [],
        [f.model_dump() for f in (scenario.factions if scenario else [])],
        p.opening_scene,
        p.style,
    )


def _interactive_session(config: EngineConfig, pack: str | None = None) -> None:
    _, name_locales, narrator_rules, world_rules, factions, _, _ = _load_pack_params(pack)
    session_dir = _create_play_session(pack=pack)
    state = _ensure_seed_generated(session_dir, pack, config)

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


def _llm_session(
    config: EngineConfig,
    max_turns: int = 20,
    pack: str | None = None,
    persona: str | None = None,
    eval_: bool = False,
) -> None:
    _, name_locales, narrator_rules, world_rules, factions, opening_scene, style = _load_pack_params(pack)
    session_dir = _create_play_session(pack=pack)
    state = _ensure_seed_generated(session_dir, pack, config)

    turns_played = 0
    trace_ids: list[str] = []

    system_prompt = (
        "You are roleplaying as a character in a text adventure game. "
        "Given the current scene and your character's motivation, "
        "decide what to do next. Respond with a short, natural language action. "
        "Do not narrate. Do not use meta-language. Just say what your character does."
    )
    if persona:
        system_prompt = (
            f"You are roleplaying as a character in a text adventure game. "
            f"Your character's persona: {persona}. "
            f"Decide what to do next. Respond with a short, natural language action. "
            f"Do not narrate. Do not use meta-language. Just say what your character does."
        )

    # Store recent turns for context (turn input + narrative)
    recent_turns: list[dict[str, str]] = []

    def _build_scenario_context(state: dict[str, Any], opening_scene: str | None, turn_num: int) -> str:
        location = state.get("location") or {}
        scene = state.get("scene") or {}
        inventory = state.get("inventory") or []
        npcs = (state.get("compendium") or {}).get("npcs") or {}

        present_npcs = []
        for npc_id, npc in npcs.items():
            if npc.get("present"):
                name = npc.get("name", npc_id)
                title = npc.get("title", "")
                note = npc.get("notes", "")
                if title:
                    present_npcs.append(f"{name} ({title})")
                elif note:
                    present_npcs.append(f"{name} ({note[:40]})")
                else:
                    present_npcs.append(name)

        inventory_items: list[str] = []
        for item in inventory:
            if isinstance(item, dict):
                inventory_items.append(str(item.get("name") or item.get("id") or ""))
            else:
                inventory_items.append(str(item))

        location_name = location.get("name", "")
        location_desc = location.get("description", "")
        scene_tagline = scene.get("tagline", "")

        has_data = location_name or present_npcs or inventory_items or scene_tagline

        if not has_data:
            return "Scenario: No scenario data loaded"

        lines = []
        if location_name:
            desc_part = f" — {location_desc}" if location_desc else ""
            lines.append(f"  Location: {location_name}{desc_part}")
        if present_npcs:
            lines.append(f"  Present: {', '.join(present_npcs[:5])}")
        if inventory_items:
            lines.append(f"  Inventory: {', '.join(inventory_items[:8])}")
        if scene_tagline:
            lines.append(f"  Scene: {scene_tagline}")

        context = "\n".join(lines)

        if turn_num <= 1 and opening_scene:
            context = f"{opening_scene.strip()}\n\n{context}"

        return f"Scenario:\n{context}"

    for turn_i in range(max_turns):
        arc = state.get("arc") or {}
        arc_goal = arc.get("visible_goal", "")

        # Build prompt: scenario context + arc goal + recent bullets + current narrative
        context_parts = []

        # Scenario context (location, NPCs, inventory, scene)
        scenario_context = _build_scenario_context(state, opening_scene, turn_i)
        context_parts.append(scenario_context)

        if arc_goal:
            context_parts.append(f"Current Goal: {arc_goal}")

        # 2-3 turns before as short bullets (player input only)
        if recent_turns:
            context_parts.append("Recent:")
            for rt in recent_turns[-3:]:
                context_parts.append(f"  - {rt['input']}")

        # Current turn narrative (full)
        if recent_turns and recent_turns[-1].get("narrative"):
            context_parts.append(f"\nNarrative:\n\n{recent_turns[-1]['narrative']}")

        user_prompt = "\n".join(context_parts) + "\n\nWhat do you do?"

        from ccya.llm_client import chat as llm_chat

        try:
            loop = _get_play_loop()
            response = loop.run_until_complete(
                llm_chat(
                    config.host,
                    config.model,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
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

        # Store this turn for next iteration
        narrative = result.get("narrative", "")
        recent_turns.append({"input": player_input, "narrative": narrative})

        state = load_state(session_dir)

    print()
    print(f"Session ended. Turns: {turns_played}")
    print(f"Traces: {', '.join(trace_ids)}")
    print(f"Events: {session_dir / 'events.jsonl'}")

    if eval_ and turns_played > 0:
        print()
        print("Running checkers on all turns...")
        from ccya.ev.events import load_events
        from ccya.ev.check import cmd_check

        events = load_events(session_dir / "events.jsonl")
        cmd_check(events, all_checkers=True, save_dir=session_dir)


def _print_missing_pack_error(flags: dict[str, str]) -> None:
    packs_dir = Path("packs")
    available = list_packs(packs_dir)
    pack_names = [p.name for p in available]
    msg = "Error: --pack is required when creating a new session (no --save-dir).\n"
    if pack_names:
        msg += f"Available packs: {', '.join(pack_names)}"
    else:
        msg += "No packs found in packs/ directory."
    print(msg, file=sys.stderr)


def cmd_play(flags: dict[str, str], args: list[str]) -> None:
    if "interactive" in flags:
        config = _build_play_config(flags)
        pack_id = flags.get("pack")
        if not pack_id and "save-dir" not in flags:
            _print_missing_pack_error(flags)
            sys.exit(1)
        _interactive_session(config, pack=pack_id)
        sys.exit(0)

    if "llm" in flags:
        config = _build_play_config(flags)
        max_turns = int(flags.get("turns", "20"))
        pack_id = flags.get("pack")
        if not pack_id and "save-dir" not in flags:
            _print_missing_pack_error(flags)
            sys.exit(1)
        _llm_session(
            config,
            max_turns=max_turns,
            pack=pack_id,
            persona=flags.get("persona"),
            eval_="eval" in flags,
        )
        sys.exit(0)

    if len(args) < 2:
        print("Usage: ev.py play <input> [--save-dir DIR] [--no-sanitize] [--model MODEL] [--temp TEMP] [--pack PACK]", file=sys.stderr)
        sys.exit(1)

    input_text = args[1]

    pack_id = flags.get("pack")
    if not pack_id and "save-dir" not in flags:
        _print_missing_pack_error(flags)
        sys.exit(1)

    _, name_locales, narrator_rules, world_rules, factions, _, _ = _load_pack_params(pack_id)
    config = _build_play_config(flags)

    if "save-dir" in flags:
        save_dir = Path(flags["save-dir"])
        state = load_state(save_dir)
    elif pack_id:
        session_dir = _create_play_session(pack=pack_id)
        save_dir = session_dir
        state = _ensure_seed_generated(session_dir, pack_id, config)
    else:
        session_dir = _create_play_session()
        save_dir = session_dir
        state = load_state(save_dir)

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
