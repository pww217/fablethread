# ev Session Config & Personality System Design

## Purpose

This document defines the session config file (`ev.yaml`), personality preset system, and CLI convenience features for the ev tooling. It is the design authority for plans implementing these changes.

## Problem Statement

The ev CLI has no session identity. Every invocation requires re-specifying `--save-dir`, events path, pack, model, temperature, sanitize flag, and persona. There is no config file that travels with a save directory. The `--persona` flag is a single free-text string with no presets or structure. The `latest` symlink is the only session discovery mechanism, and it breaks silently.

This makes iterative testing painful: `ev.py play "I search the room" --save-dir saves/ev/latest --no-sanitize --persona "aggressive mercenary" saves/ev/latest/events.jsonl` must be typed or shell-historied every time.

## Constraints

- Must not change the event schema or `events.jsonl` format.
- Must not change `state.yaml` format or `EngineConfig` structure.
- Must not change the `play_turn()` function signature or turn pipeline.
- `ev.yaml` is optional — all CLI behavior works without it.
- CLI flags always override `ev.yaml` values.
- `ev.yaml` lives in the save directory alongside `state.yaml`/`events.jsonl`.
- Must use the existing `_strip_flags()` parser — no `argparse` or third-party deps.
- Personality presets must not change the LLM extraction pipeline or ruling/narrate/storytell streams.
- Must not add shell completion scripts (out of scope).

## Non-goals

- Session sharing or multi-user support.
- `ev.yaml` for eval scenarios (eval has its own YAML structure).
- Personality system for human players (only for `--llm` mode).
- Persistent CLI aliases or shell-level completion.
- `ev.yaml` for inspection commands (`summary`, `turn`, `deltas`, etc.) — those are read-only and don't need session config.
- Migration of existing saves to use `ev.yaml`.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Session config file | `ev.yaml` in save directory with pack, model, temp, no_sanitize, turns, player section | Eliminates repetitive CLI flags; makes sessions self-describing |
| No `ev.yaml` for read commands | `ev.yaml` only affects `play`, `play --llm`, `play --interactive`, `init`, `status` | Inspection commands don't need session config; keeps scope small |
| CLI overrides `ev.yaml` | `_strip_flags()` already separates flags from positional args; flag resolution happens after `ev.yaml` load | Preserves existing CLI semantics; flags are always authoritative |
| `latest` symlink remains | `ev.yaml` is optional; `latest` symlink is the default session target | No breaking change; existing workflows continue to work |
| `--resume` flag | `ev.py play --llm --resume` loads latest save, reads `ev.yaml`, continues from `meta.turn` | Solves the "continue where I left off" problem without requiring the events path |
| Personality presets | Structured presets (`aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `custom`) with system prompt templates | Replaces free-text `--persona` with guided options; `custom` preserves free-text |
| System prompt templates | Each preset maps to a system prompt string; `custom` uses `--custom-persona` value | Keeps personality logic isolated from the LLM chat call; easy to add/remove presets |
| `ev.py init` command | Interactive scaffolding: pack, personality, model, temp → creates save dir + `ev.yaml` | Low-friction session creation; replaces the mental model of "create save dir then play" |
| `ev.py status` command | Reads `ev.yaml` + `state.yaml` from latest save, prints session dashboard | Replaces "what session am I in?" with a single command |
| `--until-error` flag | In `--llm` mode, stops playing when a turn errors out | Debugging aid for finding extraction/LLM failures |
| `ev.yaml` schema | YAML file with flat keys + nested `player` section | Simple to write by hand; matches the existing `ccya/config.yaml` pattern |

## Open Questions

- `[OPEN: System prompt text for each personality preset]` — The structure is defined (each preset maps to a system prompt string), but the actual wording for `aggressive`, `cautious`, `absurd`, `explorer`, and `driven` is not specified. This is creative/iterative — the implementer should write drafts, test them with the LLM, and refine.
- `[OPEN: `ev.yaml` gitignore]` — Sessions are test artifacts but may be worth sharing. Decision: commit by default. Document accordingly.

## Current State — What Exists

### CLI argument parsing

`ccya/ev/__init__.py` uses `_strip_flags()` — a manual token scanner that splits `sys.argv[1:]` into `flags: dict[str, str]` and `positional: list[str]`. Boolean flags get value `"true"`. The events file is auto-detected: if the last positional arg starts with `saves/`, it's used as the events path; otherwise defaults to `saves/default/events.jsonl`.

There is no `argparse`, no subcommands, no help text. The `main()` function routes `cmd` to the appropriate handler via `match/case`.

### Play command

`ccya/ev/play.py:cmd_play()` branches on flags:

- `--interactive` → `_interactive_session()` — reads stdin in a loop
- `--llm` → `_llm_session()` — LLM acts as player
- Default → single turn with `args[1]` as input text

Each mode requires `--pack` OR `--save-dir`. Session creation is `_create_play_session()`, which generates a timestamped directory under `saves/ev/` and updates the `latest` symlink.

Config is built by `_build_play_config()`, which loads `ccya/config.yaml`, applies `--model` and `--temp` overrides, and sets `sanitize_every = 0` if `--no-sanitize` is present.

### Persona handling

In `_llm_session()` (line 419-431), the system prompt is:

```
You are roleplaying as a character in a text adventure game.
Your character's persona: {persona}.
Decide what to do next. Respond with a short, natural language action.
Do not narrate. Do not use meta-language. Just say what your character does.
```

The persona is a single string injected verbatim. No presets, no structure, no guidance beyond what the user types.

### Session discovery

The `latest` symlink at `saves/ev/latest` → `saves/ev/<timestamp>_<rand>` is the only session discovery mechanism. It breaks silently if the target directory is deleted or the symlink is stale. There is no `--resume` flag or auto-detection.

### Save directory structure

Each save directory contains:
- `state.yaml` — full game state
- `events.jsonl` — immutable event log
- `chronicle.md` — human-readable narrative

No session metadata file exists. Session identity is the directory path.

### Problems with Current State

1. **No session config** — every flag must be re-stated per invocation.
2. **No `--resume`** — to continue a session, you must know the save dir or rely on `latest` symlink.
3. **Persona is unguided** — `--persona "aggressive mercenary"` works but there's no guidance on what works well.
4. **`latest` symlink is fragile** — no validation, no fallback.
5. **No session dashboard** — no way to quickly see "what session am I in?" without reading `state.yaml`.
6. **Events path is redundant** — `--save-dir saves/ev/latest` + `saves/ev/latest/events.jsonl` is the same path repeated.

## Proposed Solution

### Core Changes

#### 1. Session config file (`ev.yaml`)

New file: `saves/ev/<session>/ev.yaml`

```yaml
# ev.yaml — session configuration
pack: zombie-survival
model: qwen3-14b
temp: 0.7
no_sanitize: true
turns: 20
player:
  personality: cautious
  custom_persona: ""
```

All keys are optional. If `ev.yaml` is absent, the CLI falls back to `ccya/config.yaml` + CLI flags only.

**Resolution order** (highest to lowest priority):
1. CLI flags
2. `ev.yaml` in save directory
3. `ccya/config.yaml` (existing)

**Keys:**

| Key | Type | Default | Description |
|---|---|---|---|
| `pack` | `str` | — | Pack name (same as `--pack`) |
| `model` | `str` | — | LLM model name (same as `--model`) |
| `temp` | `float` | — | Temperature for all LLM sections (same as `--temp`) |
| `no_sanitize` | `bool` | `false` | Skip thread sanitizer (same as `--no-sanitize`) |
| `turns` | `int` | `20` | Default turn count for `--llm` mode |
| `player.personality` | `str` | `custom` | Preset name or `custom` |
| `player.custom_persona` | `str` | `""` | Free-text persona when `personality: custom` |

#### 2. Personality presets

Six presets defined in `ccya/ev/personality.py`:

| Preset | System prompt behavior |
|---|---|
| `aggressive` | Seeks combat, takes risks, pushes momentum hard. Prompt emphasizes bold actions and confrontation. |
| `cautious` | Avoids danger, investigates thoroughly, retreats from threats. Prompt emphasizes caution and information gathering. |
| `absurd` | Tests edge cases — does weird things, ignores genre norms. Prompt encourages unconventional behavior. |
| `explorer` | Prioritizes discovery, talks to NPCs, investigates environment. Prompt emphasizes exploration and interaction. |
| `driven` | Pursues the arc goal single-mindedly. Prompt emphasizes goal orientation and efficiency. |
| `custom` | Uses `player.custom_persona` value. Prompt uses the free-text string. |

Each preset maps to a system prompt string. The prompt is injected into the LLM chat call the same way `--persona` is today.

**New CLI flags:**

| Flag | Description |
|---|---|
| `--personality NAME` | Set personality preset (aggressive, cautious, absurd, explorer, driven, custom) |
| `--custom-persona TEXT` | Free-text persona string (used when `personality: custom` or overrides preset) |

Resolution: `--personality` + `--custom-persona` override `ev.yaml` `player.*` keys. `--persona` (existing) is aliased to `--personality custom --custom-persona`.

#### 3. `--resume` flag

`ev.py play --llm --resume` or `ev.py play --resume "action"`:

1. Loads `saves/ev/latest/` (validates symlink is not broken).
2. Reads `ev.yaml` if present.
3. Loads `state.yaml` to get `meta.turn`.
4. For `--llm --resume`: continues from `meta.turn + 1`.
5. For `play --resume "action"`: runs single turn.

If `saves/ev/latest` does not exist or is broken:
- `--resume` without `--save-dir`: error with list of available sessions.
- `--resume` with `--save-dir`: uses the specified directory.

#### 4. `ev.py init` command

New command: `ev.py init [--pack PACK] [--personality NAME] [--model MODEL] [--temp N] [--save-dir DIR]`

Creates a new session:
1. Generates session directory under `saves/ev/` (or uses `--save-dir`).
2. Loads pack to initialize `state.yaml` (same as `_create_play_session`).
3. Writes `ev.yaml` with the specified options.
4. Prints session path.

If `--pack` is not given:
- Lists available packs.
- If only one pack exists: uses it.
- Otherwise: errors with "specify --pack" or "available: X, Y, Z".

#### 5. `ev.py status` command

New command: `ev.py status [--save-dir DIR]`

Reads `ev.yaml` + `state.yaml` from the specified or latest save directory. Prints:

```
Session: saves/ev/20260611_143022_a1b2c3
Pack:    zombie-survival
Turn:    7
Model:   qwen3-14b
Temp:    0.7
Personality: cautious
Events:  saves/ev/20260611_143022_a1b2c3/events.jsonl
State:   saves/ev/20260611_143022_a1b2c3/state.yaml
```

If `ev.yaml` is absent: shows "Config: none (using defaults)" and omits config-derived fields.

#### 6. `--until-error` flag

New flag for `--llm` mode: `ev.py play --llm --until-error --resume`

In `--llm` mode, stops playing turns when a turn produces errors. Continues until `max_turns` or error, whichever comes first.

#### 7. Events path auto-detection

When `--save-dir` is provided, the events path is auto-detected as `<save-dir>/events.jsonl`. The events path no longer needs to be repeated as the last positional arg when `--save-dir` is present.

This is a convenience: `ev.py play "action" --save-dir saves/ev/latest` now works without the redundant `saves/ev/latest/events.jsonl` at the end.

### Alternatives Considered and Rejected

| Alternative | Why rejected |
|---|---|
| `ev.yaml` in `~/.config/ccya/` (global config) | Sessions should be self-describing; global config doesn't travel with saves |
| `ev.yaml` in cwd (project-level) | Multiple saves in one project would conflict; saves are the natural scope |
| `ev.yaml` for inspection commands | Inspection commands don't need session config; keeping it play-only reduces complexity |
| Personality as CLI enum with prompt templates in separate files | Adds file I/O complexity; presets are small strings that belong in code |
| `--resume` as default behavior (always resume latest) | Breaking change; some users want to start fresh every time |
| `ev.yaml` with full `EngineConfig` schema | Overly complex; `ev.yaml` should only contain play-relevant overrides, not every engine setting |
| Shell completion scripts | Out of scope; would require per-shell implementation (bash, zsh, fish) |

## Failure Modes and Risks

| Risk | Mitigation |
|---|---|
| `ev.yaml` is malformed YAML | `cmd_play` catches YAML parse errors, prints error with file path, exits |
| `ev.yaml` references non-existent pack | Same error as today: `_print_missing_pack_error()` |
| `ev.yaml` references non-existent model | Same error as today: LLM client fails with model not found |
| `latest` symlink is broken | `--resume` validates symlink before using; falls back to error with available sessions |
| `ev.yaml` is edited while session is active | No concurrency risk; `ev.yaml` is read once at session start |
| Personality presets become stale | Presets are simple strings; easy to update. Documented in README. |
| `--resume` resumes a session that should be abandoned | User responsibility; `--save-dir` can override `latest` |
| `ev.yaml` is committed to git | Document that `ev.yaml` should be in `.gitignore` or explicitly not commit it |

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| `--persona` flag | `ccya/ev/play.py:cmd_play()` | Replaced by `--personality` + `--custom-persona`; no backward compat |
| Redundant events path | CLI convention | When `--save-dir` is present, events path is auto-detected; events path arg is optional |

## What Is Unchanged

- `events.jsonl` format and schema.
- `state.yaml` format and schema.
- `EngineConfig` structure and `build_engine_config()`.
- `play_turn()` function signature.
- Turn pipeline (ruling → narrate → extraction → storytell).
- `_strip_flags()` parser.
- `ccya/config.yaml` structure.
- `_create_play_session()` session directory naming convention.
- `latest` symlink mechanism.
- Eval infrastructure (`ev.py eval run`, `ev.py eval list`).
- Checker infrastructure.
- Inspection commands (`summary`, `turn`, `prompt`, `deltas`, `mechanics`, `state`, `diff`, `trace`, `search`).
- `chronicle.md` generation.

## New Model Shapes

### `ev.yaml` schema

```yaml
# ev.yaml — session configuration
pack: str | null          # e.g. "zombie-survival"
model: str | null         # e.g. "qwen3-14b"
temp: float | null        # e.g. 0.7
no_sanitize: bool | null  # default: false
turns: int | null         # default: 20
player:
  personality: str | null # one of: aggressive, cautious, absurd, explorer, driven, custom
  custom_persona: str | null  # free-text persona string
```

All keys are optional. Missing keys fall back to `ccya/config.yaml` or CLI defaults.

### Personality presets

Defined in `ccya/ev/personality.py` as a dict mapping preset name to system prompt string:

```python
PERSONALITY_PROMPTS: dict[str, str] = {
    "aggressive": "...",
    "cautious": "...",
    "absurd": "...",
    "explorer": "...",
    "driven": "...",
    "custom": None,  # uses custom_persona value
}
```

Valid presets: `aggressive`, `cautious`, `absurd`, `explorer`, `driven`, `custom`.

### System prompt templates

Each preset maps to a system prompt string. The template is:

```
You are roleplaying as a character in a text adventure game.
{personality_guidance}
Decide what to do next. Respond with a short, natural language action.
Do not narrate. Do not use meta-language. Just say what your character does.
```

Where `{personality_guidance}` is replaced by the preset-specific guidance text. For `custom`, it uses `--custom-persona` or `player.custom_persona` value.

## Context for Implementing LLMs

| File | What it contains | Why it matters |
|---|---|---|
| `ccya/ev/__init__.py` | CLI entry point, `_strip_flags()`, command routing | New commands (`init`, `status`) route here; `--resume`, `--until-error` flags parsed here |
| `ccya/ev/play.py` | `cmd_play()`, `_llm_session()`, `_interactive_session()`, `_build_play_config()`, `_create_play_session()` | Session config loading, personality resolution, `--resume` logic, events path auto-detection |
| `ccya/ev/personality.py` | (new) Personality presets and system prompt templates | New file; defines `PERSONALITY_PROMPTS` dict and `resolve_personality()` function |
| `ccya/ev/init.py` | (new) `cmd_init()` for `ev.py init` command | New file; scaffolds save dir + `ev.yaml` |
| `ccya/ev/status.py` | (new) `cmd_status()` for `ev.py status` command | New file; reads `ev.yaml` + `state.yaml`, prints dashboard |
| `ccya/state/io.py` | `load_state()`, `init_save_dir()` | `status` reads `state.yaml`; `init` calls `init_save_dir()` |
| `ccya/pack.py` | `load_pack()`, `list_packs()` | `init` uses `list_packs()` to show available packs |
| `scripts/debug/README.md` | ev.py command reference | Must be updated with new commands and flags |
