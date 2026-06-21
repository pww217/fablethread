"""CLI and user configuration for CCYA.

Handles user-level defaults, persona registry, and EV/eval settings.
Engine config lives in ccya/engine/config.py.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

USER_CONFIG_DIR = Path.home() / ".config" / "ccya"
USER_CONFIG_FILE = USER_CONFIG_DIR / "config.yaml"
PERSONA_REGISTRY_FILE = USER_CONFIG_DIR / "personas.yaml"


@dataclass
class EvConfig:
    """EV/eval-specific settings."""
    model: str = "mlx-community/gemma-4-26b-a4b-it-mxfp8"
    turn_limit: int = 20
    sample_rate: float = 1.0
    checker_model: str = ""
    save_dir: str = ""


@dataclass
class PersonaConfig:
    """Player persona preset."""
    name: str
    description: str
    personality: str = ""
    style: str = ""


@dataclass
class AppConfig:
    """Top-level application config."""
    ev: EvConfig = field(default_factory=EvConfig)
    personas: list[PersonaConfig] = field(default_factory=list)


def _load_yaml(path: Path) -> dict[str, Any]:
    """Load a YAML file, returning empty dict if not found."""
    if not path.exists():
        return {}
    try:
        import yaml
        with open(path) as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        _log.warning("PyYAML not installed, config loading disabled")
        return {}
    except Exception as exc:
        _log.warning("Failed to load %s: %s", path, exc)
        return {}


def load_user_config() -> AppConfig:
    """Load user config from ~/.config/ccya/config.yaml."""
    raw = _load_yaml(USER_CONFIG_FILE)
    ev_raw = raw.get("ev", {})
    persona_raw = raw.get("persona", {})

    ev = EvConfig(
        model=ev_raw.get("model", EvConfig.model),
        turn_limit=int(ev_raw.get("turn_limit", EvConfig.turn_limit)),
        sample_rate=float(ev_raw.get("sample_rate", EvConfig.sample_rate)),
        checker_model=ev_raw.get("checker_model", EvConfig.checker_model),
        save_dir=ev_raw.get("save_dir", EvConfig.save_dir),
    )

    personas = []
    for p in persona_raw.get("presets", []):
        personas.append(PersonaConfig(
            name=p.get("name", ""),
            description=p.get("description", ""),
            personality=p.get("personality", ""),
            style=p.get("style", ""),
        ))

    return AppConfig(ev=ev, personas=personas)


def load_persona_registry() -> dict[str, PersonaConfig]:
    """Load persona registry from ~/.config/ccya/personas.yaml."""
    raw = _load_yaml(PERSONA_REGISTRY_FILE)
    registry: dict[str, PersonaConfig] = {}
    for p in raw.get("personas", []):
        name = p.get("name", "")
        if name:
            registry[name] = PersonaConfig(
                name=name,
                description=p.get("description", ""),
                personality=p.get("personality", ""),
                style=p.get("style", ""),
            )
    return registry


def resolve_persona(name: str, registry: dict[str, PersonaConfig] | None = None) -> PersonaConfig | None:
    """Resolve a persona by name from the registry."""
    if registry is None:
        registry = load_persona_registry()
    return registry.get(name)
