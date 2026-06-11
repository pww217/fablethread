# CLI Defaults and Personas — Configuration, Registry, and UX

## Purpose

Design authority for how CCYA's CLI tools (`ev.py`, `play.py`, `check.py`) configure defaults, manage personas, and surface configuration to users. Not a plan — decisions here are final and guide implementation plans.

## Problem Statement

The CLI tools have hardcoded defaults scattered across modules:

1. **No centralized config for CLI defaults.** Model endpoint, max turns, sampling rate, and other defaults are duplicated in `ccya/engine/config.py`, `ccya/ev/check.py`, and `ccya/ev/play.py`.
2. **No persona system.** The engine supports "personas" (character personalities) but the CLI has no way to select or switch between them.
3. **No persistent CLI configuration.** Every invocation requires specifying the same model endpoint, pack path, and other options.
4. **No `ev:` config section.** The engine config (`ccya/engine/config.py`) has model defaults but no dedicated section for eval-specific settings (sample rates, thresholds, checker defaults).
5. **Inconsistent flag naming.** `--model`, `--checker-model`, `--sample-rate`, `--turn-limit` — no consistent naming convention across subcommands.

## Constraints

- **Config format: YAML.** Existing engine config uses YAML (`packs/*/config.yaml`). CLI config should follow the same format.
- **Config location: `~/.config/ccya/config.yaml`** for user defaults, `packs/*/config.yaml` for pack-specific overrides.
- **No backward compatibility with old config format.** Old format is already deleted or unused.
- **Personas are engine-level concept.** The CLI surface is thin — just a way to select which persona to use. The persona system itself (`ccya/personality.py`) is out of scope.
- **ev.py is the survivor.** No new top-level CLI tools.
- **Qwen3 35B at localhost:8080/v1 is the judge model.** This is the default for all LLM-based operations (check, eval, play).

## Non-goals

- **Web UI configuration.** The web interface has its own config surface. This design covers CLI only.
- **Config validation schemas.** No JSON schema or Pydantic models for config validation. Simple YAML parsing is sufficient.
- **Config migration tools.** Old config format is already deleted.
- **Persona creation/editing.** The CLI can only select existing personas, not create or modify them.
- **Multi-model orchestration.** Always the same Qwen3 35B. No model routing or fallback logic.

## Decision Table

| Decision | What | Why |
|---|---|---|
| Single config file: `~/.config/ccya/config.yaml` | User-level defaults for model endpoint, max turns, sample rates, persona defaults | One file to edit, one file to document. Pack-specific overrides still live in `packs/*/config.yaml`. |
| `ev:` config section for eval-specific settings | `ev: {sample_rate: 1.0, threshold: 0.8, suggest: false}` | Eval settings are distinct from engine settings. Grouping them prevents config bloat in the engine section. |
| Persona registry: `~/.config/ccya/personas.yaml` | List of available personas with id, name, and engine persona label | Thin surface: the CLI reads this file and offers persona selection. The engine NPC personality system (`ccya/personality.py`) is the source of truth for persona behavior. |
| Flag naming: `--model` for engine, `--checker-model` for judge, `--sample-rate` for LLM sampling | Consistent naming across all subcommands | `--model` always means "engine model" (the game AI). `--checker-model` always means "judge model" (the eval AI). `--sample-rate` always means "LLM checker sampling rate." |
| Pack config overrides user config | `packs/*/config.yaml` takes precedence over `~/.config/ccya/config.yaml` for pack-specific settings | Each game pack can have its own defaults (e.g., different max turns, different persona). User config is the base layer. |
| No config validation | Simple YAML parsing, no Pydantic, no JSON schema | The config is small (<50 keys total). Validation adds complexity without proportional benefit. Bad config values surface as runtime errors. |
| Persona selection: `--persona <id>` flag on all subcommands | `ev.py play --persona warrior`, `ev.py check --persona warrior` | Consistent flag name across all subcommands. The persona id maps to an engine persona label via the registry. |

## Current State — What Exists

### `ccya/engine/config.py`

EngineConfig dataclass with per-stage temperatures:
- `host: "http://localhost:8080/v1"`
- `model: "mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking"`
- `ruling_temperature: 0.2`, `extract_temperature: 0.4`, `narrate_temperature: 0.9`, `generate_seed_temperature: 0.9`
- Per-stage `top_p` and `frequency_penalty` values
- No `max_turns` field, no single `temperature`/`top_p` field
- Built via `build_engine_config(cfg)` from pack YAML config

### `ccya/ev/check.py`

- `--checker-model` flag: overrides checker model name
- `--all` flag: run all registered checkers
- `--llm` flag: include LLM-based checkers
- `--save-dir` flag: path to save directory
- No `--model` flag (only `--checker-model`)
- No `--turn-limit` flag
- No persona selection
- No persistent defaults

### `ccya/ev/play.py`

- No `--model` flag in dispatch
- No `--turn-limit` flag in dispatch
- No persona selection
- No persistent defaults

### `ccya/ev/eval.py`

- `--model` flag: overrides model
- `--temp` flag: overrides temperature
- `--checkers` flag: comma-separated checker IDs
- `--report` flag: output report path (not `--report-dir`)
- No `--sample-rate` flag
- No persona selection
- No persistent defaults

### Persona system

- `ccya/personality.py` exists with NPC personality archetype registry (`NpcPersonality` dataclass, `ARCHETYPES` dict, `assign_personality()`, `validate_and_resolve()`)
- 12 NPC archetypes (cold_pragmatist, desperate_idealist, wary_opportunist, etc.)
- Archetypes are assigned to NPCs based on motivation/fear keywords
- No player persona system — this is NPC personality assignment
- No CLI surface for persona selection
- No persona registry file

### Config files

- `packs/*/config.yaml` — pack-specific config (model, max_turns, etc.)
- No user-level config file
- No `ev:` section in any config

## Proposed Solution

### Core Changes

#### 1. User config: `~/.config/ccya/config.yaml`

```yaml
# ~/.config/ccya/config.yaml

# Engine defaults
engine:
  model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking
  endpoint: localhost:8080/v1
  max_turns: 20
  temperature: 0.7
  top_p: 0.9

# Eval-specific defaults
ev:
  sample_rate: 1.0
  threshold: 0.8
  suggest: false
  report_dir: reports/eval
  llm_model: mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking
  llm_endpoint: localhost:8080/v1

# Persona defaults
persona:
  default: warrior
  registry: ~/.config/ccya/personas.yaml
```

#### 2. Persona registry: `~/.config/ccya/personas.yaml`

```yaml
# ~/.config/ccya/personas.yaml

personas:
  - id: warrior
    name: "Warrior"
    engine_label: warrior
    description: "Combat-focused character with high momentum tolerance"
  - id: scholar
    name: "Scholar"
    engine_label: scholar
    description: "Knowledge-focused character with high pacing sensitivity"
  - id: rogue
    name: "Rogue"
    engine_label: rogue
    description: "Stealth-focused character with high condition resilience"
```

The CLI reads this file and:
1. Lists available personas: `ev.py personas list`
2. Validates persona selection: `ev.py play --persona invalid` → error
3. Maps persona id to engine label: `warrior` → `warrior` (engine_label)

#### 3. Config loading: `ccya/config.py` (new)

```python
# ccya/config.py

import yaml
from pathlib import Path
from dataclasses import dataclass, field

USER_CONFIG_PATH = Path.home() / ".config" / "ccya" / "config.yaml"
PERSONA_REGISTRY_PATH = Path.home() / ".config" / "ccya" / "personas.yaml"

@dataclass
class EngineConfig:
    model: str = "mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking"
    endpoint: str = "localhost:8080/v1"
    max_turns: int = 20
    temperature: float = 0.7
    top_p: float = 0.9

@dataclass
class EvConfig:
    sample_rate: float = 1.0
    threshold: float = 0.8
    suggest: bool = False
    report_dir: str = "reports/eval"
    llm_model: str = "mlx-community/Qwen3.6-35B-A3B-OptiQ-4bit-thinking"
    llm_endpoint: str = "localhost:8080/v1"

@dataclass
class PersonaConfig:
    default: str = "warrior"
    registry: str = "~/.config/ccya/personas.yaml"

@dataclass
class AppConfig:
    engine: EngineConfig = field(default_factory=EngineConfig)
    ev: EvConfig = field(default_factory=EvConfig)
    persona: PersonaConfig = field(default_factory=PersonaConfig)

def load_user_config() -> AppConfig:
    """Load ~/.config/ccya/config.yaml, falling back to defaults."""
    if not USER_CONFIG_PATH.exists():
        return AppConfig()
    with open(USER_CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    return AppConfig(
        engine=EngineConfig(**data.get("engine", {})),
        ev=EvConfig(**data.get("ev", {})),
        persona=PersonaConfig(**data.get("persona", {})),
    )

def load_pack_config(pack_path: Path) -> dict:
    """Load pack-specific config.yaml, overriding user defaults."""
    config_path = pack_path / "config.yaml"
    if not config_path.exists():
        return {}
    with open(config_path) as f:
        return yaml.safe_load(f) or {}

def load_persona_registry() -> list[dict]:
    """Load persona registry from ~/.config/ccya/personas.yaml."""
    registry_path = Path(PERSONA_REGISTRY_PATH)
    if not registry_path.exists():
        return []
    with open(registry_path) as f:
        data = yaml.safe_load(f) or {}
    return data.get("personas", [])
```

#### 4. CLI flag updates

All subcommands adopt consistent flag naming. Existing flags preserved, new flags added:

| Subcommand | Flag | Default Source | Description |
|---|---|---|---|
| `ev.py play` | `--model` | `config.engine.model` | Engine model (game AI) |
| `ev.py play` | `--turn-limit` | `config.engine.max_turns` | Max turns for this session (NEW) |
| `ev.py play` | `--persona` | `config.persona.default` | Persona to use (NEW) |
| `ev.py check` | `--checker-model` | `config.ev.llm_model` | Judge model (eval AI) (existing) |
| `ev.py check` | `--turn-limit` | `config.engine.max_turns` | Max turns to check (NEW) |
| `ev.py check` | `--persona` | `config.persona.default` | Persona to use for context (NEW) |
| `ev.py eval run` | `--sample-rate` | `config.ev.sample_rate` | LLM checker sampling rate (NEW) |
| `ev.py eval run` | `--report` | `config.ev.report_dir` | Output report path (existing, rename from path to dir concept) |
| `ev.py eval run` | `--persona` | `config.persona.default` | Persona to use for context (NEW) |
| `ev.py personas list` | (none) | `config.persona.registry` | List available personas |

#### 5. New command: `ev.py personas`

```bash
# List available personas
ev.py personas list

# List with details
ev.py personas list --verbose

# Validate a persona id
ev.py personas validate warrior
```

Implementation: thin wrapper around `load_persona_registry()`. No engine interaction.

#### 6. Config override precedence

```
CLI flag > Pack config > User config > Hardcoded defaults
```

Example:
```bash
# CLI flag overrides everything
ev.py play --model custom-model --turn-limit 10

# Pack config overrides user config for pack-specific settings
# (packs/my-pack/config.yaml: max_turns: 30)
ev.py play  # uses max_turns: 30 from pack config

# User config overrides hardcoded defaults
# (~/.config/ccya/config.yaml: max_turns: 25)
ev.py play --pack packs/other-pack  # uses max_turns: 25 from user config
```

### Alternatives Considered and Rejected

1. **JSON config format.**
   Rejected: YAML is already used for pack configs and prompt templates. Consistency matters.

2. **Environment variables for config.**
   Rejected: `CCYA_MODEL=...` is less discoverable than `~/.config/ccya/config.yaml`. Environment variables are for CI/production, not local development.

3. **Config validation with Pydantic.**
   Rejected: The config is small (<50 keys). Validation adds complexity without proportional benefit. Bad values surface as runtime errors.

4. **Persona creation via CLI.**
    Rejected: Persona creation is an engine-level operation (modifying `ccya/personality.py` data). The CLI surface should be thin — just selection, not creation.

5. **Multiple persona registry files.**
   Rejected: One registry file (`~/.config/ccya/personas.yaml`) is sufficient. Pack-specific personas would be managed via the engine, not the CLI.

## Failure Modes and Risks

1. **Config file doesn't exist.** `load_user_config()` returns defaults. No error. This is intentional — the tool should work out of the box.

2. **Persona id doesn't exist in registry.** `ev.py play --persona invalid` → error: "Persona 'invalid' not found in registry." No fallback to default.

3. **Pack config conflicts with user config.** Pack config takes precedence for pack-specific settings. This is intentional — the pack author knows their game best.

4. **Config file is malformed YAML.** `yaml.safe_load()` raises `YAMLError`. The error message should be clear: "Failed to parse ~/.config/ccya/config.yaml: <error details>."

5. **Persona registry is empty.** `ev.py personas list` returns "No personas configured." The engine still works — personas are optional.

## What Is Removed

| Removed | From | Notes |
|---|---|---|
| Hardcoded model defaults in `ccya/engine/config.py` | `ccya/engine/config.py` | Replaced by `ccya/config.py` with YAML loading |
| Redundant flag naming in `ccya/ev/check.py` | `ccya/ev/check.py` | `--checker-model` preserved, consistent with `--model` for engine |
| Hardcoded defaults in `ccya/ev/play.py` | `ccya/ev/play.py` | Replaced by `ccya/config.py` loading |
| Hardcoded defaults in `ccya/ev/eval.py` | `ccya/ev/eval.py` | Replaced by `ccya/config.py` loading |

## What Is Unchanged

- `ccya/personality.py` — NPC personality archetype registry unchanged
- `ccya/ev/play.py` — play command logic unchanged (only flag defaults change)
- `ccya/ev/check.py` — check command logic unchanged (only flag defaults change)
- `ccya/ev/eval.py` — eval command logic unchanged (only flag defaults change)
- `ccya/engine/config.py` — model config defaults unchanged (but loading moved to `ccya/config.py`)
- Pack config format (`packs/*/config.yaml`) — unchanged, still YAML

## New Model Shapes

```python
# ccya/config.py — new module (user-level config, separate from ccya/engine/config.py EngineConfig)

@dataclass
class EngineConfig:
    model: str
    host: str
    max_turns: int
    temperature: float
    top_p: float

@dataclass
class EvConfig:
    sample_rate: float
    threshold: float
    suggest: bool
    report_dir: str
    llm_model: str
    llm_endpoint: str

@dataclass
class PersonaConfig:
    default: str
    registry: str

@dataclass
class AppConfig:
    engine: EngineConfig
    ev: EvConfig
    persona: PersonaConfig

# Persona registry format (YAML)
# ~/.config/ccya/personas.yaml
personas:
  - id: warrior
    name: "Warrior"
    engine_label: warrior
    description: "Combat-focused character"
```

## Context for Implementing LLMs

- `ccya/config.py` — new module for config loading. Creates `AppConfig` with `EngineConfig`, `EvConfig`, `PersonaConfig`.
- `ccya/engine/config.py` — remove hardcoded defaults. Import from `ccya/config.py` instead.
- `ccya/ev/play.py` — update flag defaults to use `ccya/config.py` loading.
- `ccya/ev/check.py` — update flag defaults to use `ccya/config.py` loading. `--checker-model` preserved.
- `ccya/ev/eval.py` — update flag defaults to use `ccya/config.py` loading.
- `ccya/ev/personas.py` — new module for `ev.py personas` command. Thin wrapper around `ccya/config.py` persona registry loading.
- `~/.config/ccya/config.yaml` — new user config file. Created on first run if missing.
- `~/.config/ccya/personas.yaml` — new persona registry file. Created on first run if missing.
