# ev Session Config & Personality System Plan

## Purpose

Implement session config (`ev.yaml`), personality presets, `--resume`, `--until-error`, `ev.py init`, `ev.py status`, and events path auto-detection for the ev CLI.

## Problem Statement

The ev CLI has no session identity. Every invocation requires re-specifying `--save-dir`, events path, pack, model, temperature, sanitize flag, and persona. There is no config file that travels with a save directory. The `--persona` flag is a single free-text string with no presets or structure. The `latest` symlink is the only session discovery mechanism, and it breaks silently. This makes iterative testing painful.

## Constraints

- Must not change the event schema or `events.jsonl` format.
- Must not change `state.yaml` format or `EngineConfig` structure.
- Must not change the `play_turn()` function signature or turn pipeline.
- `ev.yaml` is optional — all CLI behavior works without it.
- CLI flags always override `ev.yaml` values.
- `ev.yaml` lives in the save directory alongside `state.yaml`/`events.jsonl`.
- Must use the existing `_strip_flags()` parser — no `argparse` or third-party deps.
- Personality presets must not change the LLM extraction pipeline or ruling/narrate/storytell streams.
- No backward compat for `--persona` — remove it entirely.
- `ev.yaml` is committed by default (not gitignored).

## Non-goals

- Session sharing or multi-user support.
- `ev.yaml` for eval scenarios.
- Personality system for human players (only for `--llm` mode).
- Shell completion scripts.
- `ev.yaml` for inspection commands.
- Migration of existing saves to use `ev.yaml`.

## Solution

Add a session config file (`ev.yaml`) that travels with save directories, a personality preset system with six presets, `--resume`/`--until-error` flags, `ev.py init`/`ev.py status` commands, and events path auto-detection when `--save-dir` is present. Remove the `--persona` flag entirely.

## Firm decisions

1. `ev.yaml` resolution order: CLI flags > `ev.yaml` > `ccya/config.yaml`.
2. Six personality presets: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `custom`.
3. `--persona` is removed entirely; replaced by `--personality` + `--custom-persona`.
4. `--resume` loads `saves/ev/latest/` by default; `--save-dir` overrides.
5. `ev.py init` creates save dir + `ev.yaml` from CLI args.
6. `ev.py status` reads `ev.yaml` + `state.yaml` from latest or `--save-dir`.
7. `--until-error` stops `--llm` mode on first error turn.
8. Events path auto-detected from `--save-dir` when events path arg is omitted.
9. `ev.yaml` is committed by default.

## Risks, Ambiguities, and Blockers

- **Personality prompt wording** is iterative — the implementer must write drafts, test with the LLM, and refine. This is the only creative/iterative part of the plan.
- **`--resume` with broken `latest` symlink** — the error message must list available sessions. The `list_packs()` function is already available; a new `list_sessions()` helper is needed.
- **`ev.yaml` YAML parse errors** — must be caught gracefully with file path and line number.
- **`_ensure_seed_generated` fragility** — `cmd_init()` imports the private `_ensure_seed_generated` from `play.py`. For scenario packs it generates the seed; for static packs `_create_play_session` already wrote `state.yaml` and `_ensure_seed_generated` just loads it back. This is correct but fragile. Recommendation: extract the seed-generation logic from `_ensure_seed_generated` into a public `init_save_dir_from_pack()` helper in `ccya/pack.py` or `ccya/state/io.py` that `init.py` and `play.py` both call.

## Status
`completed`

## Phases

Three phases: (1) core infrastructure — session config loading + personality presets + CLI flag changes, (2) new commands — `init` + `status`, (3) events path auto-detection + `--resume`/`--until-error` + cleanup + docs.

## Implementation — Phase 1: Core infrastructure

### Context files to load
- `ccya/ev/__init__.py` — CLI entry point, `_strip_flags()`, command routing
- `ccya/ev/play.py` — `cmd_play()`, `_llm_session()`, `_interactive_session()`, `_build_play_config()`, `_create_play_session()`
- `ccya/state/io.py` — `load_state()`, `init_save_dir()`
- `ccya/pack.py` — `load_pack()`, `list_packs()`
- `ccya/models.py` — `load_config()`
- `ccya/engine/config.py` — `build_engine_config()`

### Detailed steps

#### Step 1.1 — Create `ccya/ev/personality.py`

**File:** `ccya/ev/personality.py`

**What:** New file defining personality presets and system prompt resolution.

```python
VALID_PERSONALITIES: list[str] = ["aggressive", "cautious", "absurd", "explorer", "driven", "custom"]

PERSONALITY_PROMPTS: dict[str, str] = {
    "aggressive": "Your character is aggressive: bold, confrontational, risk-taking. Push for momentum through direct action and confrontation. Don't hesitate — strike first.",
    "cautious": "Your character is cautious: careful, methodical, risk-averse. Gather information before acting. Avoid unnecessary danger. Retreat from threats.",
    "absurd": "Your character is absurd: unconventional, unpredictable, boundary-pushing. Ignore genre norms. Do the unexpected. Test the edges of the world.",
    "explorer": "Your character is an explorer: curious, thorough, discovery-driven. Talk to NPCs. Investigate the environment. Prioritize learning over combat.",
    "driven": "Your character is driven: focused, goal-oriented, efficient. Pursue the arc goal single-mindedly. Don't get distracted by side paths.",
}
```

`resolve_personality(personality: str, custom_persona: str | None) -> str` returns the system prompt:
- For presets: `"You are roleplaying as a character in a text adventure game.\n{prompt}\nDecide what to do next. Respond with a short, natural language action.\nDo not narrate. Do not use meta-language. Just say what your character does."`
- For `custom`: `"You are roleplaying as a character in a text adventure game.\nYour character's persona: {custom_persona}.\nDecide what to do next. Respond with a short, natural language action.\nDo not narrate. Do not use meta-language. Just say what your character does."`

**Why:** Isolates personality logic from the LLM chat call. Easy to add/remove presets.

**Validation:**
```bash
.venv/bin/python -c "from ccya.ev.personality import resolve_personality; print(resolve_personality('aggressive', None))"
.venv/bin/python -c "from ccya.ev.personality import resolve_personality; print(resolve_personality('custom', 'a paranoid botanist'))"
.venv/bin/python -c "from ccya.ev.personality import VALID_PERSONALITIES; assert set(VALID_PERSONALITIES) == {'aggressive','cautious','absurd','explorer','driven','custom'}"
```

#### Step 1.2 — Create `ccya/ev/session_config.py`

**File:** `ccya/ev/session_config.py`

**What:** New file for loading `ev.yaml` from a save directory.

```python
from pathlib import Path
from typing import Any

def load_session_config(save_dir: Path) -> dict[str, Any] | None:
    """Load ev.yaml from save_dir. Returns None if file doesn't exist."""
    ev_yaml = save_dir / "ev.yaml"
    if not ev_yaml.exists():
        return None
    import yaml
    with open(ev_yaml) as f:
        data = yaml.safe_load(f) or {}
    return data
```

`resolve_flag(flags: dict[str, str], session_config: dict[str, Any] | None, key: str, default: Any = None) -> Any` — resolution: CLI flag > session_config > default.

`resolve_player_config(flags: dict[str, str], session_config: dict[str, Any] | None) -> dict[str, str]` — returns `{"personality": ..., "custom_persona": ...}` with resolution: CLI `--personality`/`--custom-persona` > session_config `player.*` > defaults.

**Why:** Encapsulates `ev.yaml` loading and resolution logic. Session config is optional — returns `None` if absent.

**Validation:**
```bash
.venv/bin/python -c "
from pathlib import Path
from ccya.ev.session_config import load_session_config
# Test with non-existent file
result = load_session_config(Path('/tmp/nonexistent'))
assert result is None
"
```

#### Step 1.3 — Modify `ccya/ev/play.py` — personality + session config

**File:** `ccya/ev/play.py`

**What:**
1. Import `resolve_personality` from `ccya.ev.personality` and `load_session_config`, `resolve_flag`, `resolve_player_config` from `ccya.ev.session_config`.
2. In `_llm_session()`:
   - Remove the hardcoded `system_prompt` construction (lines 419-431).
   - Accept `personality: str | None` and `custom_persona: str | None` parameters.
   - Call `resolve_personality(personality or "custom", custom_persona)` to build the system prompt.
3. In `cmd_play()` for all modes (`--llm`, `--interactive`, single-turn):
   - Parse `--personality` and `--custom-persona` flags.
   - Load `ev.yaml` from the save directory (or `latest` if `--resume`).
   - Resolve personality: CLI flags > session_config > default `custom`.
   - Call `_build_play_config(flags, session_config)` with session config.
   - Pass resolved personality to the session function.
4. In `_build_play_config()`:
   - Accept `session_config: dict[str, Any] | None`.
   - Apply `model`, `temp`, `no_sanitize` from session_config if not overridden by CLI flags.
   - Resolution: CLI flag > session_config > `ccya/config.yaml`.

**Why:** Session config is the source of truth for pack/model/temp/sanitize/personality when CLI flags are absent. The `--interactive` mode creates its session directory inside `_interactive_session()`, so `cmd_play()` must load `ev.yaml` from the save directory after the session is created and before building the config. Personality presets replace `--persona`.

**Validation:**
```bash
# Verify _llm_session accepts personality + custom_persona
.venv/bin/python -c "
import inspect
from ccya.ev.play import _llm_session
sig = inspect.signature(_llm_session)
params = list(sig.parameters.keys())
assert 'personality' in params
assert 'custom_persona' in params
"
```

#### Step 1.4 — Modify `ccya/ev/play.py` — remove `--persona`

**File:** `ccya/ev/play.py`

**What:**
1. Remove `--persona` flag handling from `cmd_play()` (the `persona=flags.get("persona")` argument to `_llm_session()`).
2. Remove `persona: str | None` parameter from `_llm_session()` signature.
3. Replace with `personality: str | None` and `custom_persona: str | None`.

**Why:** `--persona` is removed entirely per design decision.

**Validation:**
```bash
# Verify --persona is no longer referenced
.venv/bin/python -c "
import ast
with open('ccya/ev/play.py') as f:
    tree = ast.parse(f.read())
code = open('ccya/ev/play.py').read()
assert '--persona' not in code
assert 'persona' not in code or 'personality' in code  # allow 'personality' references
"
```

#### Step 1.5 — Modify `ccya/ev/__init__.py` — add new flags

**File:** `ccya/ev/__init__.py`

**What:**
1. In `cmd_play` case (line 196-198): pass `personality` and `custom_persona` from flags to `cmd_play()`.
2. The flags `--personality` and `--custom-persona` are already parsed by `_strip_flags()` — no parser changes needed.
3. Document the new flags in the `main()` error message (line 77).

**Why:** New CLI flags need to reach `cmd_play()`. `_strip_flags()` already handles them.

**Validation:**
```bash
# Verify flags are parsed
.venv/bin/python -c "
from ccya.ev import _strip_flags
flags, pos = _strip_flags(['play', '--personality', 'aggressive', '--custom-persona', 'test', 'action'])
assert flags['personality'] == 'aggressive'
assert flags['custom-persona'] == 'test'
assert pos == ['play', 'action']
"
```

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.

## Implementation — Phase 2: New commands

### Context files to load
- `ccya/ev/__init__.py` — CLI entry point, command routing
- `ccya/ev/play.py` — `_create_play_session()`, `_load_pack_params()`, `_build_play_config()`
- `ccya/state/io.py` — `load_state()`, `init_save_dir()`
- `ccya/pack.py` — `load_pack()`, `list_packs()`
- `ccya/ev/session_config.py` — `load_session_config()`

### Detailed steps

#### Step 2.1 — Create `ccya/ev/init.py`

**File:** `ccya/ev/init.py`

**What:** New file with `cmd_init(flags: dict[str, str], args: list[str]) -> None`.

```python
def cmd_init(flags: dict[str, str], args: list[str]) -> None:
    """Create a new session: save dir + ev.yaml."""
    from pathlib import Path
    import yaml
    
    pack = flags.get("pack")
    personality = flags.get("personality")
    model = flags.get("model")
    temp = flags.get("temp")
    save_dir_str = flags.get("save-dir")
    
    # Determine save directory
    if save_dir_str:
        save_dir = Path(save_dir_str)
    else:
        # Use _create_play_session from play.py
        from ccya.ev.play import _create_play_session
        save_dir = _create_play_session(pack=pack)
    
    # If --pack given, initialize state
    if pack:
        from ccya.ev.play import _build_play_config, _ensure_seed_generated
        config = _build_play_config(flags)
        _ensure_seed_generated(save_dir, pack, config)
    
    # Write ev.yaml
    ev_config: dict[str, Any] = {}
    if pack:
        ev_config["pack"] = pack
    if model:
        ev_config["model"] = model
    if temp:
        ev_config["temp"] = float(temp)
    if personality:
        ev_config["player"] = {"personality": personality}
    
    if ev_config:
        ev_yaml_path = save_dir / "ev.yaml"
        with open(ev_yaml_path, "w") as f:
            yaml.dump(ev_config, f, default_flow_style=False)
    
    print(f"Session created: {save_dir}")
    if ev_config:
        print(f"Config: {ev_yaml_path}")
```

If `--pack` is not given:
- List available packs via `list_packs()`.
- If only one pack: use it implicitly.
- Otherwise: error with "specify --pack" + list available packs.

**Why:** Low-friction session creation. Replaces "create save dir then play" mental model.

**Validation:**
```bash
# Create a session with init
.venv/bin/python scripts/debug/ev.py init --pack zombie-survival --personality cautious
ls saves/ev/latest/ev.yaml
cat saves/ev/latest/ev.yaml
```

#### Step 2.2 — Create `ccya/ev/status.py`

**File:** `ccya/ev/status.py`

**What:** New file with `cmd_status(flags: dict[str, str]) -> None`.

```python
def cmd_status(flags: dict[str, str]) -> None:
    """Print session dashboard."""
    import sys
    from pathlib import Path
    from ccya.ev.session_config import load_session_config
    from ccya.state.io import load_state
    
    save_dir_str = flags.get("save-dir")
    if save_dir_str:
        save_dir = Path(save_dir_str)
    else:
        latest = Path("saves/ev/latest")
        if not latest.exists():
            print("Error: no session found. Run 'ev.py init' or specify --save-dir.", file=sys.stderr)
            sys.exit(1)
        save_dir = latest
    
    state = load_state(save_dir)
    session_config = load_session_config(save_dir)
    
    print(f"Session: {save_dir}")
    print(f"Turn:    {state.get('meta', {}).get('turn', '?')}")
    
    if session_config:
        if session_config.get("pack"):
            print(f"Pack:    {session_config['pack']}")
        if session_config.get("model"):
            print(f"Model:   {session_config['model']}")
        if session_config.get("temp"):
            print(f"Temp:    {session_config['temp']}")
        player = session_config.get("player", {})
        if player.get("personality"):
            print(f"Personality: {player['personality']}")
    
    print(f"Events:  {save_dir / 'events.jsonl'}")
    print(f"State:   {save_dir / 'state.yaml'}")
```

If `ev.yaml` is absent: print "Config: none (using defaults)" and omit config-derived fields.

**Why:** Replaces "what session am I in?" with a single command.

**Validation:**
```bash
# Check status of latest session
.venv/bin/python scripts/debug/ev.py status
```

#### Step 2.3 — Modify `ccya/ev/__init__.py` — route new commands

**File:** `ccya/ev/__init__.py`

**What:**
1. Add `case "init":` and `case "status":` to the `match cmd:` block.
2. Route to `cmd_init(flags, args)` and `cmd_status(flags)` respectively.

**Why:** New commands need CLI entry points.

**Validation:**
```bash
# Verify commands are routed
.venv/bin/python -c "
from ccya.ev import main
# Just verify the module loads without errors
"
```

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.

## Implementation — Phase 3: Events path auto-detection + --resume/--until-error + cleanup + docs

### Context files to load
- `ccya/ev/__init__.py` — CLI entry point, events path detection
- `ccya/ev/play.py` — `cmd_play()`, `_llm_session()`, `_interactive_session()`
- `ccya/ev/session_config.py` — `load_session_config()`

### Detailed steps

#### Step 3.1 — Events path auto-detection

**File:** `ccya/ev/__init__.py`

**What:**

`main()` currently extracts the events path from the last positional arg before routing to `cmd_play` (lines 85-89). But `cmd_play` never uses the loaded `events` object — the events file is written by `play_turn()` into the save directory. This means the events path extraction is entirely redundant for `play`.

1. In `main()`, when `cmd == "play"`: skip the events path extraction entirely. Don't pop the last positional arg. Pass all positional args to `cmd_play` as-is.

**Why:** Eliminates the redundant events path argument. `ev.py play "action" --save-dir saves/ev/latest` now works without the trailing `saves/ev/latest/events.jsonl`.

**Validation:**
```bash
# These should now be equivalent:
.venv/bin/python scripts/debug/ev.py play "action" --save-dir saves/ev/latest
.venv/bin/python scripts/debug/ev.py play "action" --save-dir saves/ev/latest saves/ev/latest/events.jsonl
```

#### Step 3.2 — `--resume` flag

**File:** `ccya/ev/__init__.py` + `ccya/ev/play.py`

**What:**
1. In `main()`: parse `--resume` flag.
2. In `cmd_play()`:
   - If `--resume` is present and `--save-dir` is not:
     - Load `saves/ev/latest/`.
     - Validate symlink is not broken: `if not (save_dir / "state.yaml").exists(): error + list available sessions`.
   - If `--resume` is present with `--save-dir`: use the specified directory.
   - Load `ev.yaml` from the resolved save directory.
   - For `--llm --resume`: set `max_turns` to `meta.turn + 20` (same relative cap as starting fresh). If `--turns N` is also specified, run exactly N turns from the resumed position.
   - For `play --resume "action"`: run single turn.
   - For `--interactive --resume`: print error `"--resume is not supported with --interactive mode"` and exit.

**Why:** Solves "continue where I left off" without requiring the events path.

**Validation:**
```bash
# Resume latest session
.venv/bin/python scripts/debug/ev.py play --llm --resume
```

#### Step 3.3 — `--until-error` flag

**File:** `ccya/ev/play.py`

**What:**
1. In `_llm_session()`:
   - Accept `until_error: bool = False` parameter.
   - In the turn loop: after `play_turn()`, check `result.get("errors")`.
   - If `until_error` is True and errors exist: break the loop.
   - Print a message: "Stopped due to errors on turn N."

**Why:** Debugging aid for finding extraction/LLM failures.

**Validation:**
```bash
# Play until first error
.venv/bin/python scripts/debug/ev.py play --llm --until-error --resume
```

#### Step 3.4 — Update `scripts/debug/README.md`

**File:** `scripts/debug/README.md`

**What:**
1. Add `ev.yaml` section: explain the file format, resolution order, and that it's committed by default.
2. Update `play` command section:
   - Replace `--persona` with `--personality` + `--custom-persona`.
   - Document `--resume`, `--until-error`.
   - Document events path auto-detection.
3. Add `init` command section.
4. Add `status` command section.
5. Update "Common pitfalls" section.

**Why:** Documentation is mandatory per AGENTS.md.

**Validation:**
```bash
# Verify README is updated
grep -c "personality" scripts/debug/README.md
grep -c "resume" scripts/debug/README.md
grep -c "init" scripts/debug/README.md
grep -c "status" scripts/debug/README.md
grep -c "ev.yaml" scripts/debug/README.md
```

#### Step 3.5 — Update `docs/repomap.md`

**File:** `docs/repomap.md`

**What:**
1. Add `ccya/ev/personality.py` to the ev module section.
2. Add `ccya/ev/session_config.py` to the ev module section.
3. Add `ccya/ev/init.py` to the ev module section.
4. Add `ccya/ev/status.py` to the ev module section.
5. Update `ccya/ev/play.py` section: note `personality` + `custom_persona` parameters, `until_error` parameter.
6. Update CLI argument section: note `--personality`, `--custom-persona`, `--resume`, `--until-error`.

**Why:** Documentation is mandatory per AGENTS.md.

**Validation:**
```bash
# Verify repomap is updated
grep -c "personality" docs/repomap.md
grep -c "session_config" docs/repomap.md
grep -c "init.py" docs/repomap.md
grep -c "status.py" docs/repomap.md
```

#### Step 3.6 — Update `AGENTS.md`

**File:** `AGENTS.md`

**What:**
1. Update "Known LLM extraction issues" section if personality presets change error patterns.
2. Update ev.py usage examples to use `--personality` instead of `--persona`.
3. Document `ev.py init` and `ev.py status` commands.
4. Document `ev.yaml` convention.

**Why:** Documentation is mandatory per AGENTS.md.

**Validation:**
```bash
# Verify AGENTS.md is updated
grep -c "personality" AGENTS.md
grep -c "init" AGENTS.md
grep -c "status" AGENTS.md
grep -c "ev.yaml" AGENTS.md
```

### Tests to write or update

None — tests are temporarily removed during refactor per AGENTS.md.
