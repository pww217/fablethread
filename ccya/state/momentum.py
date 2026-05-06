"""Momentum application from rules bands."""

from __future__ import annotations

from typing import Any

from ccya.rules import MOMENTUM_DELTA

_MOMENTUM_MIN: int = -3
_MOMENTUM_MAX: int = 3


def apply_momentum(state: dict[str, Any], band: str) -> None:
    """Update pc.momentum deterministically from a rules band.

    Clamped to [-3, +3]. Mutates state in place.
    """
    pc = state.setdefault("pc", {})
    current = int(pc.get("momentum", 0))
    delta = MOMENTUM_DELTA.get(band, 0)
    pc["momentum"] = max(_MOMENTUM_MIN, min(_MOMENTUM_MAX, current + delta))
