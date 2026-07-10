"""CLI and eval settings for CCYA.

Engine config lives in ccya/engine/config.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EvConfig:
    """EV/eval-specific settings.
    
    Model precedence: CLI flag > session config > engine config (config.yaml) > engine default (google/gemma-4-26b-a4b-it).
    """
    turn_limit: int = 20
    sample_rate: float = 1.0


@dataclass
class AppConfig:
    """Top-level application config."""
    ev: EvConfig = field(default_factory=EvConfig)


def get_ev_config() -> EvConfig:
    """Return default EV config (CLI flags override at runtime)."""
    return EvConfig()
