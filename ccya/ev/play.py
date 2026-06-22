from __future__ import annotations

import asyncio
import logging
import sys
import time
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

from ccya.ev.personality import resolve_personality
from ccya.ev.session_config import load_session_config, resolve_player_config

_log = logging.getLogger(__name__)

EV_SAVES_DIR = Path("evals/runs")

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

    scene = {
        "tags": state_after.get("scene", {}).get("tags", []),
        "session_name": state_after.get("meta", {}).get("session_name", ""),
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
        "actions": [],
        "scene": {
            "tags": state.get("scene", {}).get("tags", []),
            "session_name": state.get("meta", {}).get("session_name", ""),
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
        lines.append(f"Ruling:    {ruling.get('intent_verb', '?').upper()} (skill: {skill}, diff: {diff})")
        if ruling.get("rolled"):
            dice = ruling.get("dice", "?")
            lines.append(f"           Roll: {dice} -> Band: {band}")

    narrative = result.get("narrative", "")
    lines.append(f"Narrative: \"{narrative[:60]}{'...' if len(narrative) > 60 else ''}\" ({len(narrative)} chars)")
    lines.append("")

    actions = result.get("actions", [])
    lines.append(f"Actions:   {', '.join(actions) if actions else 'none'}")

    scene = result.get("scene", {})
    scene_session_name = scene.get("session_name", "")
    scene_id = scene.get("id", "")
    scene_parts = [s for s in [scene_id, scene_session_name] if s]
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


def _get_git_info() -> dict[str, str | bool]:
    """Return git tag, sha, branch, and dirty flag. All fields default to 'no-repo'."""
    import subprocess
    info: dict[str, str | bool] = {
        "git_tag": "no-repo",
        "git_sha": "no-repo",
        "git_branch": "no-repo",
        "git_dirty": True,
    }
    try:
        info["git_sha"] = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        info["git_branch"] = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        info["git_tag"] = subprocess.check_output(
            ["git", "describe", "--tags", "--always"], stderr=subprocess.DEVNULL, text=True
        ).strip()
        info["git_dirty"] = bool(subprocess.check_output(
            ["git", "status", "--porcelain"], stderr=subprocess.DEVNULL, text=True
        ).strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return info


def _write_run_meta(session_dir: Path, pack: str | None, persona: str | None, max_turns: int) -> None:
    """Write run-meta.yaml into the session directory."""
    import yaml
    git = _get_git_info()
    meta = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "git_sha": git["git_sha"],
        "git_branch": git["git_branch"],
        "git_tag": git["git_tag"],
        "git_dirty": git["git_dirty"],
        "pack": pack or "unknown",
        "personality": persona or "unknown",
        "max_turns": max_turns,
        "actual_turns": None,
        "duration_ms": None,
        "pass_rate": None,
    }
    meta_path = session_dir / "run-meta.yaml"
    with open(meta_path, "w") as f:
        yaml.dump(meta, f, default_flow_style=False, sort_keys=False)


def _create_play_session(
    pack: str | None = None,
    packs_dir: Path | None = None,
    personality: str | None = None,
    max_turns: int = 20,
) -> Path:
    now = datetime.now()

    # Build grouping dir: YYYY-MM-DD_{tag}_{sha8}
    git = _get_git_info()
    tag = str(git["git_tag"])
    sha = str(git["git_sha"])
    group_name = now.strftime("%Y-%m-%d") + f"_{tag}_{sha}"

    # Build run dir: HHMM_{pack}_{persona}_{max_turns}t
    pack_label = pack or "unknown"
    persona_label = personality or "unknown"
    run_name = now.strftime("%H%M") + f"_{pack_label}_{persona_label}_{max_turns}t"

    group_dir = EV_SAVES_DIR / group_name
    session_dir = group_dir / run_name
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

    _write_run_meta(session_dir, pack, personality, max_turns)

    latest_link = EV_SAVES_DIR / "latest"
    if latest_link.is_symlink() or latest_link.exists():
        latest_link.unlink()
    relative_target = str(Path(group_name) / run_name)
    latest_link.symlink_to(relative_target)

    return session_dir


def _build_play_config(flags: dict[str, str], session_config: dict[str, Any] | None = None) -> EngineConfig:
    from ccya.config import load_user_config

    user_cfg = load_user_config()
    raw_cfg = load_config()

    # Model precedence: CLI flag > session config > user config > hardcoded
    if "model" in flags:
        raw_cfg.setdefault("llm", {})["model"] = flags["model"]
    elif session_config is not None and "model" in session_config:
        raw_cfg.setdefault("llm", {})["model"] = str(session_config["model"])
    elif user_cfg.ev.model:
        raw_cfg.setdefault("llm", {})["model"] = user_cfg.ev.model

    if "temp" in flags:
        temp = float(flags["temp"])
        for section in ("ruling", "extract", "narrate", "generate_seed"):
            raw_cfg.setdefault("llm", {}).setdefault(section, {})["temperature"] = temp
    elif session_config is not None and "temp" in session_config:
        temp = float(session_config["temp"])
        for section in ("ruling", "extract", "narrate", "generate_seed"):
            raw_cfg.setdefault("llm", {}).setdefault(section, {})["temperature"] = temp

    config = build_engine_config(raw_cfg)

    if "no-sanitize" in flags:
        config.sanitize_every = 0
    elif session_config is not None:
        no_sanitize = session_config.get("no_sanitize", session_config.get("no-sanitize"))
        if no_sanitize:
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
    personality: str | None = None,
    custom_persona: str | None = None,
    eval_: bool = False,
    until_error: bool = False,
    save_dir: Path | None = None,
    auto_report: bool = False,
    llm_checkers: bool = False,
) -> None:
    _, name_locales, narrator_rules, world_rules, factions, _, style = _load_pack_params(pack)

    if save_dir is not None:
        state = load_state(save_dir)
    else:
        session_dir = _create_play_session(pack=pack, personality=personality, max_turns=max_turns)
        state = _ensure_seed_generated(session_dir, pack, config)
        save_dir = session_dir

    turns_played = 0
    trace_ids: list[str] = []

    arc_goal = (state.get("arc") or {}).get("visible_goal", "")
    system_prompt = resolve_personality(personality or "custom", custom_persona, arc_goal=arc_goal)

    # Store recent turns for context (turn input + narrative)
    recent_turns: list[dict[str, str]] = []

    for turn_i in range(max_turns):
        context_parts = []

        # Inventory (mechanical state for decision-making)
        inv = state.get("inventory") or []
        if inv:
            items = []
            for item in inv:
                if isinstance(item, dict):
                    items.append(str(item.get("name") or item.get("id") or ""))
                else:
                    items.append(str(item))
            context_parts.append(f"Inventory: {', '.join(items)}")

        # Arc goal + threads (narrative direction)
        arc = state.get("arc") or {}
        goal = arc.get("visible_goal", "")
        if goal:
            context_parts.append(f"Goal: {goal}")

        # Current narrative (what just happened)
        if recent_turns and recent_turns[-1].get("narrative"):
            context_parts.append(recent_turns[-1]["narrative"])

        if context_parts:
            user_prompt = "\n\n".join(context_parts) + "\n\nWhat do you do?"
        else:
            user_prompt = "What do you do?"

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
            player_input, state, config, save_dir,
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

        if until_error and result.get("errors"):
            print(f"Stopped due to errors on turn {turn_i + 1}.")
            break

        # Store this turn for next iteration
        narrative = result.get("narrative", "")
        recent_turns.append({"input": player_input, "narrative": narrative})

        state = load_state(save_dir)

    print()
    print(f"Session ended. Turns: {turns_played}")
    print(f"Traces: {', '.join(trace_ids)}")
    print(f"Events: {save_dir / 'events.jsonl'}")

    if eval_ and turns_played > 0:
        print()
        print("Running checkers on all turns...")
        from ccya.ev.events import load_events
        from ccya.ev.checkers import CheckerResult, list_checkers, run_checkers
        from ccya.ev.eval import _store_checker_warnings, _build_rubric_areas, _compute_pass_rate

        events = load_events(save_dir / "events.jsonl")

        runner_checkers = [m["id"] for m in list_checkers(checker_type="deterministic")]
        checker_results: dict[str, CheckerResult] = run_checkers(runner_checkers, events, save_dir=save_dir)

        if llm_checkers:
            llm_checker_ids = [m["id"] for m in list_checkers(checker_type="llm")]
            llm_results = run_checkers(llm_checker_ids, events, save_dir=save_dir)
            checker_results.update(llm_results)

        _store_checker_warnings(checker_results, events, save_dir)

        if auto_report:
            rubric_areas = _build_rubric_areas(checker_results)
            pass_rate = _compute_pass_rate(checker_results)
            report_path = save_dir / "CONSOLIDATED-REPORT.md"
            from jinja2 import Environment, FileSystemLoader
            from datetime import datetime, timezone
            template_dir = Path("evals/ev-tooling/templates")
            env = Environment(loader=FileSystemLoader(str(template_dir)), keep_trailing_newline=True)
            template = env.get_template("report.md.j2")
            git_sha = "unknown"
            git_branch = "unknown"
            try:
                import subprocess
                git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()[:7]
            except Exception:
                pass
            try:
                import subprocess
                git_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
            except Exception:
                pass
            report_ctx = {
                "pack": pack or "unknown",
                "personality": personality or "unknown",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "git_sha": git_sha,
                "git_branch": git_branch,
                "actual_turns": turns_played,
                "max_turns": max_turns,
                "duration_ms": 0,
                "pass_rate": pass_rate,
                "rubric_areas": rubric_areas,
                "prev_run": None,
                "pass_rate_delta": 0.0,
            }
            report_content = template.render(**report_ctx)
            report_path.write_text(report_content)
            print(f"Report written to {report_path}")


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
        if "resume" in flags:
            print("--resume is not supported with --interactive mode", file=sys.stderr)
            sys.exit(1)
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

        # Handle --resume
        save_dir: Path | None = None
        if "resume" in flags:
            if "save-dir" in flags:
                save_dir = Path(flags["save-dir"])
            else:
                save_dir = EV_SAVES_DIR / "latest"
            if not (save_dir / "state.yaml").exists():
                print(f"Error: --resume: no valid session at {save_dir}", file=sys.stderr)
                print("Available sessions:", file=sys.stderr)
                if EV_SAVES_DIR.exists():
                    for d in sorted(EV_SAVES_DIR.iterdir()):
                        if d.is_dir() or d.is_symlink():
                            print(f"  {d}", file=sys.stderr)
                else:
                    print(f"  ({EV_SAVES_DIR} does not exist)", file=sys.stderr)
                sys.exit(1)
            state = load_state(save_dir)
            session_config = load_session_config(save_dir)
            player_cfg = resolve_player_config(flags, session_config)
            max_turns = state.get("meta", {}).get("turn", 0) + 20
            if "turns" in flags:
                max_turns = state.get("meta", {}).get("turn", 0) + int(flags["turns"])
        else:
            session_config = None
            player_cfg = {"personality": "custom", "custom_persona": None}

        _llm_session(
            config,
            max_turns=max_turns,
            pack=pack_id,
            personality=player_cfg["personality"],
            custom_persona=player_cfg["custom_persona"],
            eval_="eval" in flags,
            until_error="until-error" in flags,
            save_dir=save_dir if "resume" in flags else None,
            auto_report="auto-report" in flags,
            llm_checkers="llm-checkers" in flags,
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
        session_dir = _create_play_session(pack=pack_id, max_turns=2)
        save_dir = session_dir
        state = _ensure_seed_generated(session_dir, pack_id, config)
    else:
        session_dir = _create_play_session(max_turns=2)
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
